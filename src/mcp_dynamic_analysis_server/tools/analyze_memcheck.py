from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore, generate_run_id
from ..core.command_builder import build_memcheck_command
from ..core.exceptions import RunnerError, ValidationError
from ..core.normalizer import normalize_memcheck
from ..core.parser_memcheck import parse_memcheck
from ..core.runner import ensure_valgrind_available, run_command
from ..core.validators import sanitize_env, validate_cwd, validate_executable, validate_paths
from ..models.requests import AnalyzeMemcheckRequest
from ..models.responses import AnalyzeMemcheckResponse, ArtifactPaths


def analyze_memcheck(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()

    try:
        request = AnalyzeMemcheckRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    target_path = validate_executable(request.target_path, settings.workspace_root)
    cwd = validate_cwd(request.cwd, settings.workspace_root)
    suppression_paths = validate_paths(request.suppressions, settings.workspace_root, "suppression")

    env = sanitize_env(request.env)
    env = {**os.environ, **env}

    store = ArtifactStore(settings.runs_dir)
    run_id = generate_run_id()
    artifacts = store.create_run_dir(run_id)

    store.write_json(artifacts.request_path, request.model_dump())

    ensure_valgrind_available(settings.valgrind_bin)
    build = build_memcheck_command(
        valgrind_bin=settings.valgrind_bin,
        target_path=target_path,
        run_dir=artifacts.run_dir,
        args=request.args,
        track_origins=request.track_origins,
        leak_check=request.leak_check,
        show_leak_kinds=request.show_leak_kinds,
        suppressions=suppression_paths,
        xml_enabled=request.xml,
    )

    store.write_text(artifacts.command_path, shlex.join(build.command))

    execution = run_command(
        command=build.command,
        cwd=cwd,
        env=env,
        stdin=request.stdin,
        timeout_sec=request.timeout_sec,
        stdout_path=artifacts.stdout_path,
        stderr_path=artifacts.stderr_path,
    )

    raw_errors = []
    if artifacts.xml_path.exists():
        try:
            raw_errors = parse_memcheck(artifacts.xml_path)
        except Exception as exc:
            raise RunnerError(f"Failed to parse Valgrind XML: {exc}") from exc

    normalized = normalize_memcheck(run_id, raw_errors, artifacts.xml_path, artifacts.log_path)

    store.write_json(artifacts.normalized_report_path, normalized.model_dump())
    store.write_json(
        artifacts.summary_path,
        {
            "run_id": run_id,
            "tool": "memcheck",
            "stats": normalized.stats.model_dump(),
            "top_findings": [f.model_dump() for f in normalized.findings[:5]],
        },
    )
    store.write_json(
        artifacts.metadata_path,
        {
            "run_id": run_id,
            "tool": "memcheck",
            "exit_code": execution.exit_code,
            "timed_out": execution.timed_out,
            "duration_sec": execution.duration_sec,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
        },
    )

    top_findings = normalized.findings[:5]
    response = AnalyzeMemcheckResponse(
        run_id=run_id,
        status="completed" if not execution.timed_out else "timed_out",
        tool="memcheck",
        exit_code=execution.exit_code,
        timed_out=execution.timed_out,
        error_exit_code_triggered=execution.exit_code == 42,
        stats=normalized.stats,
        top_findings=top_findings,
        artifacts=ArtifactPaths(
            run_dir=str(artifacts.run_dir),
            report_path=str(artifacts.normalized_report_path),
            xml_path=str(artifacts.xml_path),
            log_path=str(artifacts.log_path),
            stdout_path=str(artifacts.stdout_path),
            stderr_path=str(artifacts.stderr_path),
        ),
    )
    return json.loads(response.model_dump_json())

from __future__ import annotations

import json
import os
import shlex
from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore, generate_run_id
from ..core.exceptions import RunnerError, ValidationError
from ..core.normalizer_asan import normalize_asan
from ..core.parser_asan import parse_asan_log
from ..core.runner import run_command
from ..core.validators import sanitize_env, validate_cwd, validate_executable
from ..models.requests import AsanRunRequest
from ..models.responses import AnalyzeMemcheckResponse, ArtifactPaths


def asan_run(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()

    try:
        request = AsanRunRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    target_path = validate_executable(request.target_path, settings.workspace_root)
    cwd = validate_cwd(request.cwd, settings.workspace_root)

    env = sanitize_env(request.env)
    env = {**os.environ, **env}
    if request.asan_options:
        env["ASAN_OPTIONS"] = request.asan_options
    if request.lsan_options:
        env["LSAN_OPTIONS"] = request.lsan_options

    store = ArtifactStore(settings.runs_dir)
    run_id = generate_run_id()
    artifacts = store.create_run_dir(run_id)

    store.write_json(artifacts.request_path, request.model_dump())
    store.write_text(artifacts.command_path, shlex.join([str(target_path), *request.args]))

    execution = run_command(
        command=[str(target_path), *request.args],
        cwd=cwd,
        env=env,
        stdin=request.stdin,
        timeout_sec=request.timeout_sec,
        stdout_path=artifacts.stdout_path,
        stderr_path=artifacts.stderr_path,
    )

    try:
        stderr_text = artifacts.stderr_path.read_text(encoding="utf-8", errors="replace")
        raw_errors = parse_asan_log(stderr_text)
    except Exception as exc:
        raise RunnerError(f"Failed to parse ASan output: {exc}") from exc

    normalized = normalize_asan(run_id, raw_errors, artifacts.stderr_path)

    store.write_json(artifacts.normalized_report_path, normalized.model_dump())
    store.write_json(
        artifacts.summary_path,
        {
            "run_id": run_id,
            "tool": "asan",
            "stats": normalized.stats.model_dump(),
            "top_findings": [f.model_dump() for f in normalized.findings[:5]],
        },
    )
    store.write_json(
        artifacts.metadata_path,
        {
            "run_id": run_id,
            "tool": "asan",
            "exit_code": execution.exit_code,
            "timed_out": execution.timed_out,
            "duration_sec": execution.duration_sec,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
        },
    )

    response = AnalyzeMemcheckResponse(
        run_id=run_id,
        status="completed" if not execution.timed_out else "timed_out",
        tool="asan",
        exit_code=execution.exit_code,
        timed_out=execution.timed_out,
        error_exit_code_triggered=execution.exit_code != 0,
        stats=normalized.stats,
        top_findings=normalized.findings[:5],
        artifacts=ArtifactPaths(
            run_dir=str(artifacts.run_dir),
            report_path=str(artifacts.normalized_report_path),
            xml_path="",
            log_path=str(artifacts.stderr_path),
            stdout_path=str(artifacts.stdout_path),
            stderr_path=str(artifacts.stderr_path),
        ),
    )
    return json.loads(response.model_dump_json())

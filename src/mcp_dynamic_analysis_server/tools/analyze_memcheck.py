from __future__ import annotations

import json
import os
import shlex
import stat
from pathlib import Path
from typing import Any, Dict
import logging

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_registry import ArtifactRegistry
from ..core.artifact_store import ArtifactStore, generate_run_id
from ..core.command_builder import build_memcheck_command
from ..core.downloader import download_file
from ..core.exceptions import RunnerError, ValidationError
from ..core.normalizer import normalize_memcheck
from ..core.parser_memcheck import parse_memcheck
from ..core.r2_client import R2Client, R2Config
from ..core.runner import ensure_valgrind_available, run_command
from ..core.validators import sanitize_env, validate_cwd, validate_executable, validate_paths
from ..models.requests import AnalyzeMemcheckRequest
from ..models.responses import AnalyzeMemcheckResponse, ArtifactPaths


def analyze_memcheck(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    logger = logging.getLogger("mcp_dynamic_analysis_server")

    try:
        request = AnalyzeMemcheckRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    if not request.target_path and not request.target_url and not request.artifact_id:
        raise ValidationError("One of target_path, target_url, or artifact_id is required")
    if request.target_url and request.artifact_id:
        raise ValidationError("Provide only one of target_url or artifact_id")
    cwd = validate_cwd(request.cwd, settings.workspace_root)
    suppression_paths = validate_paths(request.suppressions, settings.workspace_root, "suppression")

    env = sanitize_env(request.env)
    env = {**os.environ, **env}

    store = ArtifactStore(settings.runs_dir)
    run_id = generate_run_id()
    artifacts = store.create_run_dir(run_id)

    store.write_json(artifacts.request_path, request.model_dump())

    ensure_valgrind_available(settings.valgrind_bin)

    logger.info(
        "Analyze request run_id=%s source=%s target_path=%s target_url=%s artifact_id=%s",
        run_id,
        "artifact_id" if request.artifact_id else "target_url" if request.target_url else "target_path",
        request.target_path,
        _safe_url_host(request.target_url),
        request.artifact_id,
    )

    target_path = _resolve_target_path(request, settings, artifacts.run_dir)
    target_path = validate_executable(str(target_path), settings.workspace_root)
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


def _resolve_target_path(
    request: AnalyzeMemcheckRequest,
    settings: Any,
    run_dir: Path,
) -> Path:
    logger = logging.getLogger("mcp_dynamic_analysis_server")
    if request.target_path and not request.target_url and not request.artifact_id:
        return Path(request.target_path).expanduser().resolve()

    dest_dir = run_dir / "inputs"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = "uploaded_binary"
    download_url = request.target_url
    expected_sha256 = request.target_sha256

    if request.artifact_id:
        if not all(
            [
                settings.r2_endpoint,
                settings.r2_access_key_id,
                settings.r2_secret_access_key,
                settings.r2_bucket,
            ]
        ):
            raise ValidationError("R2 credentials are not configured")
        registry = ArtifactRegistry(settings.artifacts_dir)
        record = registry.get_record(request.artifact_id)
        filename = record.filename
        if record.sha256 and not expected_sha256:
            expected_sha256 = record.sha256
        r2 = R2Client(
            R2Config(
                endpoint=settings.r2_endpoint or "",
                access_key_id=settings.r2_access_key_id or "",
                secret_access_key=settings.r2_secret_access_key or "",
                bucket=settings.r2_bucket or "",
                region=settings.r2_region,
                use_ssl=settings.r2_use_ssl,
                presign_expires_sec=settings.r2_presign_expires_sec,
                upload_prefix=settings.r2_upload_prefix,
                request_timeout_sec=settings.r2_healthcheck_timeout_sec,
            )
        )
        download_url = r2.presign_get(record.key)
    elif request.target_url:
        parsed_name = Path(request.target_url.split("?", 1)[0]).name
        if parsed_name:
            filename = parsed_name

    dest_path = dest_dir / filename
    timeout = request.download_timeout_sec or settings.r2_download_timeout_sec
    allow_hosts = settings.r2_allow_hosts or None
    if not download_url:
        raise ValidationError("No download URL available for target")
    download_file(
        url=download_url,
        dest=dest_path,
        max_bytes=settings.r2_max_upload_bytes,
        timeout_sec=timeout,
        expected_sha256=expected_sha256,
        allow_hosts=allow_hosts,
    )
    dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    try:
        size_bytes = dest_path.stat().st_size
    except OSError:
        size_bytes = None
    logger.info(
        "Downloaded artifact to %s size_bytes=%s source=%s",
        dest_path,
        size_bytes,
        "artifact_id" if request.artifact_id else "target_url",
    )
    return dest_path


def _safe_url_host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        from urllib.parse import urlparse

        return urlparse(url).hostname
    except Exception:
        return None

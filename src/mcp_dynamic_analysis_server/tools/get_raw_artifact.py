from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore
from ..core.exceptions import ArtifactNotFound, ValidationError
from ..models.requests import RawArtifactRequest
from ..models.responses import RawArtifactResponse


ARTIFACT_MAP = {
    "xml": "valgrind.xml",
    "log": "valgrind.log",
    "stdout": "stdout.txt",
    "stderr": "stderr.txt",
    "request": "request.json",
    "command": "command.txt",
    "normalized_report": "normalized_report.json",
    "summary": "summary.json",
    "metadata": "metadata.json",
}


def get_raw_artifact(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    try:
        request = RawArtifactRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    filename = ARTIFACT_MAP.get(request.artifact_type)
    if not filename:
        raise ValidationError(f"Unsupported artifact_type: {request.artifact_type}")

    path = settings.runs_dir / request.run_id / filename
    store = ArtifactStore(settings.runs_dir)

    try:
        content = store.read_text(path, max_bytes=settings.max_artifact_preview_bytes)
        size_bytes = path.stat().st_size if path.exists() else None
    except ArtifactNotFound as exc:
        raise ValidationError(str(exc)) from exc

    truncated = False
    if size_bytes is not None and size_bytes > settings.max_artifact_preview_bytes:
        truncated = True

    response = RawArtifactResponse(
        run_id=request.run_id,
        artifact_type=request.artifact_type,
        path=str(path),
        content=content,
        truncated=truncated,
        size_bytes=size_bytes,
    )
    return response.model_dump()

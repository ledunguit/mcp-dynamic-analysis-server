from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore
from ..core.exceptions import ArtifactNotFound, ValidationError
from ..models.requests import GetReportRequest


def get_report(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    try:
        request = GetReportRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    store = ArtifactStore(settings.runs_dir)
    report_path = settings.runs_dir / request.run_id / "normalized_report.json"
    try:
        return store.read_json(report_path)
    except ArtifactNotFound as exc:
        raise ValidationError(str(exc)) from exc

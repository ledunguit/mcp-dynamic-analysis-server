from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore
from ..core.exceptions import ArtifactNotFound, ValidationError
from ..models.findings import Finding
from ..models.requests import ListFindingsRequest
from ..models.responses import ListFindingsResponse


def list_findings(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    try:
        request = ListFindingsRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    store = ArtifactStore(settings.runs_dir)
    report_path = settings.runs_dir / request.run_id / "normalized_report.json"
    try:
        report = store.read_json(report_path)
    except ArtifactNotFound as exc:
        raise ValidationError(str(exc)) from exc

    findings = [Finding.model_validate(item) for item in report.get("findings", [])]

    filtered = []
    for finding in findings:
        if request.severity and finding.severity != request.severity:
            continue
        if request.kind and finding.kind != request.kind:
            continue
        if request.file and finding.location.file != request.file:
            continue
        if request.function and finding.location.function != request.function:
            continue
        filtered.append(finding)

    limited = filtered[: request.limit]

    response = ListFindingsResponse(
        run_id=request.run_id,
        count=len(filtered),
        findings=limited,
    )
    return response.model_dump()

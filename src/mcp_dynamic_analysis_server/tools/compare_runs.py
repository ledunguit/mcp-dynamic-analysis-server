from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_store import ArtifactStore
from ..core.compare import compare_findings
from ..core.exceptions import ArtifactNotFound, ValidationError
from ..models.findings import Finding
from ..models.requests import CompareRunsRequest
from ..models.responses import CompareRunsResponse, CompareRunsSummary


def compare_runs(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    try:
        request = CompareRunsRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    store = ArtifactStore(settings.runs_dir)
    base_path = settings.runs_dir / request.base_run_id / "normalized_report.json"
    new_path = settings.runs_dir / request.new_run_id / "normalized_report.json"

    try:
        base_report = store.read_json(base_path)
        new_report = store.read_json(new_path)
    except ArtifactNotFound as exc:
        raise ValidationError(str(exc)) from exc

    base_findings = [Finding.model_validate(item) for item in base_report.get("findings", [])]
    new_findings = [Finding.model_validate(item) for item in new_report.get("findings", [])]

    fixed, added, persistent = compare_findings(base_findings, new_findings)

    response = CompareRunsResponse(
        base_run_id=request.base_run_id,
        new_run_id=request.new_run_id,
        summary=CompareRunsSummary(
            fixed=len(fixed),
            new=len(added),
            persistent=len(persistent),
        ),
        fixed_findings=fixed,
        new_findings=added,
        persistent_findings=persistent,
    )
    return response.model_dump()

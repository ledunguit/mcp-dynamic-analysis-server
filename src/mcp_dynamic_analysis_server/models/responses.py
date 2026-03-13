from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .findings import Finding, FindingStats


class ArtifactPaths(BaseModel):
    run_dir: str
    report_path: str
    xml_path: str
    log_path: str
    stdout_path: str
    stderr_path: str


class AnalyzeMemcheckResponse(BaseModel):
    run_id: str
    status: str
    tool: str
    exit_code: int
    timed_out: bool
    error_exit_code_triggered: bool
    stats: FindingStats
    top_findings: List[Finding]
    artifacts: ArtifactPaths


class ListFindingsResponse(BaseModel):
    run_id: str
    count: int
    findings: List[Finding]


class CompareRunsSummary(BaseModel):
    fixed: int
    new: int
    persistent: int


class CompareRunsResponse(BaseModel):
    base_run_id: str
    new_run_id: str
    summary: CompareRunsSummary
    fixed_findings: List[Finding]
    new_findings: List[Finding]
    persistent_findings: List[Finding]


class RawArtifactResponse(BaseModel):
    run_id: str
    artifact_type: str
    path: str
    content: Optional[str] = None
    truncated: bool = False
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

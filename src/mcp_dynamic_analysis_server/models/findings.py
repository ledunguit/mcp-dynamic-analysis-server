from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StackFrame(BaseModel):
    function: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None


class FindingLocation(BaseModel):
    file: Optional[str] = None
    line: Optional[int] = None
    function: Optional[str] = None


class FindingEvidence(BaseModel):
    xml_path: Optional[str] = None
    log_path: Optional[str] = None


class Finding(BaseModel):
    finding_id: str
    tool: str
    kind: str
    severity: str
    confidence: str
    message: str
    location: FindingLocation
    stack: List[StackFrame] = Field(default_factory=list)
    aux: Dict[str, Any] = Field(default_factory=dict)
    origin: Dict[str, Any] = Field(default_factory=dict)
    evidence: FindingEvidence
    signature: str


class FindingStats(BaseModel):
    finding_count: int
    high: int
    medium: int
    low: int


class NormalizedReport(BaseModel):
    run_id: str
    tool: str
    findings: List[Finding]
    stats: FindingStats
    generated_at: str

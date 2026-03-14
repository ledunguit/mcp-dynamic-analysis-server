from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class AnalyzeMemcheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_path: Optional[str] = None
    target_url: Optional[str] = None
    artifact_id: Optional[str] = None
    target_sha256: Optional[str] = None
    download_timeout_sec: Optional[int] = None
    args: List[str] = Field(default_factory=list)
    cwd: Optional[str] = None
    timeout_sec: int = Field(default=60, gt=0, le=3600)
    track_origins: bool = True
    leak_check: str = "full"
    show_leak_kinds: str = "all"
    xml: bool = True
    suppressions: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    stdin: Optional[str] = None
    labels: List[str] = Field(default_factory=list)


class GetReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str


class ListFindingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    severity: Optional[str] = None
    kind: Optional[str] = None
    file: Optional[str] = None
    function: Optional[str] = None
    limit: int = Field(default=50, gt=0, le=1000)


class CompareRunsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_run_id: str
    new_run_id: str


class RawArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    artifact_type: str


class CreateUploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = None
    expires_sec: Optional[int] = None


class AsanRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_path: str
    args: List[str] = Field(default_factory=list)
    cwd: Optional[str] = None
    timeout_sec: int = Field(default=60, gt=0, le=3600)
    env: Dict[str, str] = Field(default_factory=dict)
    stdin: Optional[str] = None
    asan_options: Optional[str] = None
    lsan_options: Optional[str] = None
    labels: List[str] = Field(default_factory=list)

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .artifact_store import ArtifactStore


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    key: str
    filename: str
    content_type: str | None
    size_bytes: int | None
    sha256: str | None
    created_at: str


class ArtifactRegistry:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._store = ArtifactStore(self.base_dir)

    def create_record(
        self,
        key: str,
        filename: str,
        content_type: str | None,
        size_bytes: int | None,
        sha256: str | None,
        artifact_id: str | None = None,
    ) -> ArtifactRecord:
        artifact_id = artifact_id or uuid.uuid4().hex
        created_at = _timestamp()
        record = ArtifactRecord(
            artifact_id=artifact_id,
            key=key,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256,
            created_at=created_at,
        )
        record_dir = self.base_dir / artifact_id
        record_dir.mkdir(parents=True, exist_ok=False)
        self._store.write_json(record_dir / "metadata.json", record.__dict__)
        return record

    def get_record(self, artifact_id: str) -> ArtifactRecord:
        record_path = self.base_dir / artifact_id / "metadata.json"
        data: Dict[str, Any] = self._store.read_json(record_path)
        return ArtifactRecord(
            artifact_id=data["artifact_id"],
            key=data["key"],
            filename=data["filename"],
            content_type=data.get("content_type"),
            size_bytes=data.get("size_bytes"),
            sha256=data.get("sha256"),
            created_at=data.get("created_at"),
        )


def _timestamp() -> str:
    from time import gmtime, strftime

    return strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())

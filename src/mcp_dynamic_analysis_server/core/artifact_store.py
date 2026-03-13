from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ArtifactNotFound


@dataclass(frozen=True)
class ArtifactPaths:
    run_dir: Path
    request_path: Path
    command_path: Path
    stdout_path: Path
    stderr_path: Path
    xml_path: Path
    log_path: Path
    normalized_report_path: Path
    summary_path: Path
    metadata_path: Path


def generate_run_id() -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"{_timestamp()}-{suffix}"


def _timestamp() -> str:
    from time import gmtime, strftime

    return strftime("%Y%m%d-%H%M%S", gmtime())


class ArtifactStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run_dir(self, run_id: str) -> ArtifactPaths:
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        return ArtifactPaths(
            run_dir=run_dir,
            request_path=run_dir / "request.json",
            command_path=run_dir / "command.txt",
            stdout_path=run_dir / "stdout.txt",
            stderr_path=run_dir / "stderr.txt",
            xml_path=run_dir / "valgrind.xml",
            log_path=run_dir / "valgrind.log",
            normalized_report_path=run_dir / "normalized_report.json",
            summary_path=run_dir / "summary.json",
            metadata_path=run_dir / "metadata.json",
        )

    def write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def read_text(self, path: Path, max_bytes: Optional[int] = None) -> str:
        if not path.exists():
            raise ArtifactNotFound(f"Artifact not found: {path}")
        if max_bytes is None:
            return path.read_text(encoding="utf-8", errors="replace")
        with path.open("rb") as handle:
            data = handle.read(max_bytes)
        return data.decode("utf-8", errors="replace")

    def read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise ArtifactNotFound(f"Artifact not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[str]:
        if not self.base_dir.exists():
            return []
        return sorted([p.name for p in self.base_dir.iterdir() if p.is_dir()])

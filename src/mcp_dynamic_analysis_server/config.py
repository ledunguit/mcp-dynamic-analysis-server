from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    workspace_root: Path
    runs_dir: Path
    valgrind_bin: str
    max_artifact_bytes: int
    max_artifact_preview_bytes: int


def _default_workspace_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[3]


def load_settings() -> Settings:
    workspace_root = Path(os.environ.get("WORKSPACE_ROOT", _default_workspace_root())).resolve()
    runs_dir = Path(os.environ.get("RUNS_DIR", workspace_root / "runs")).resolve()
    valgrind_bin = os.environ.get("VALGRIND_BIN", "valgrind")
    max_artifact_bytes = int(os.environ.get("MAX_ARTIFACT_BYTES", "2000000"))
    max_artifact_preview_bytes = int(os.environ.get("MAX_ARTIFACT_PREVIEW_BYTES", "20000"))
    return Settings(
        workspace_root=workspace_root,
        runs_dir=runs_dir,
        valgrind_bin=valgrind_bin,
        max_artifact_bytes=max_artifact_bytes,
        max_artifact_preview_bytes=max_artifact_preview_bytes,
    )

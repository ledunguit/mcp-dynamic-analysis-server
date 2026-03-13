from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from .exceptions import ValidationError


def _ensure_within_root(path: Path, workspace_root: Path) -> None:
    try:
        path.relative_to(workspace_root)
    except ValueError as exc:
        raise ValidationError(f"Path '{path}' is outside WORKSPACE_ROOT") from exc


def validate_executable(path_str: str, workspace_root: Path) -> Path:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise ValidationError(f"Target path not found: {path}")
    _ensure_within_root(path, workspace_root)
    if not path.is_file():
        raise ValidationError(f"Target path is not a file: {path}")
    if not os.access(path, os.X_OK):
        raise ValidationError(f"Target path is not executable: {path}")
    return path


def validate_cwd(cwd: Optional[str], workspace_root: Path) -> Optional[Path]:
    if not cwd:
        return None
    path = Path(cwd).expanduser().resolve()
    if not path.exists():
        raise ValidationError(f"cwd not found: {path}")
    _ensure_within_root(path, workspace_root)
    if not path.is_dir():
        raise ValidationError(f"cwd is not a directory: {path}")
    return path


def validate_paths(paths: Iterable[str], workspace_root: Path, label: str) -> list[Path]:
    resolved: list[Path] = []
    for p in paths:
        path = Path(p).expanduser().resolve()
        if not path.exists():
            raise ValidationError(f"{label} not found: {path}")
        _ensure_within_root(path, workspace_root)
        resolved.append(path)
    return resolved


def sanitize_env(env: dict[str, str]) -> dict[str, str]:
    clean: dict[str, str] = {}
    for key, value in env.items():
        if not key or "\x00" in key or "\x00" in value:
            raise ValidationError("Invalid environment variable key/value")
        clean[str(key)] = str(value)
    return clean

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    workspace_root: Path
    runs_dir: Path
    artifacts_dir: Path
    valgrind_bin: str
    max_artifact_bytes: int
    max_artifact_preview_bytes: int
    r2_endpoint: str | None
    r2_access_key_id: str | None
    r2_secret_access_key: str | None
    r2_bucket: str | None
    r2_region: str
    r2_use_ssl: bool
    r2_presign_expires_sec: int
    r2_upload_prefix: str
    r2_max_upload_bytes: int
    r2_download_timeout_sec: int
    r2_allow_hosts: List[str]
    r2_healthcheck_on_startup: bool
    r2_healthcheck_timeout_sec: int


def _default_workspace_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[3]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def load_settings() -> Settings:
    default_root = _default_workspace_root()
    _load_dotenv(default_root / ".env")
    workspace_root = Path(os.environ.get("WORKSPACE_ROOT", default_root)).resolve()
    if workspace_root != default_root:
        _load_dotenv(workspace_root / ".env")
    runs_dir = Path(os.environ.get("RUNS_DIR", workspace_root / "runs")).resolve()
    artifacts_dir = Path(os.environ.get("ARTIFACTS_DIR", workspace_root / "artifacts")).resolve()
    valgrind_bin = os.environ.get("VALGRIND_BIN", "valgrind")
    max_artifact_bytes = int(os.environ.get("MAX_ARTIFACT_BYTES", "2000000"))
    max_artifact_preview_bytes = int(os.environ.get("MAX_ARTIFACT_PREVIEW_BYTES", "20000"))
    r2_endpoint = os.environ.get("R2_ENDPOINT")
    r2_access_key_id = os.environ.get("R2_ACCESS_KEY_ID")
    r2_secret_access_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    r2_bucket = os.environ.get("R2_BUCKET")
    r2_region = os.environ.get("R2_REGION", "auto")
    r2_use_ssl = os.environ.get("R2_USE_SSL", "true").lower() == "true"
    r2_presign_expires_sec = int(os.environ.get("R2_PRESIGN_EXPIRES_SEC", "900"))
    r2_upload_prefix = os.environ.get("R2_UPLOAD_PREFIX", "uploads")
    r2_max_upload_bytes = int(os.environ.get("R2_MAX_UPLOAD_BYTES", "20000000"))
    r2_download_timeout_sec = int(os.environ.get("R2_DOWNLOAD_TIMEOUT_SEC", "60"))
    allow_hosts_raw = os.environ.get("R2_ALLOW_HOSTS", "")
    r2_allow_hosts = [h.strip() for h in allow_hosts_raw.split(",") if h.strip()]
    r2_healthcheck_on_startup = os.environ.get("R2_HEALTHCHECK_ON_STARTUP", "false").lower() == "true"
    r2_healthcheck_timeout_sec = int(os.environ.get("R2_HEALTHCHECK_TIMEOUT_SEC", "5"))
    return Settings(
        workspace_root=workspace_root,
        runs_dir=runs_dir,
        artifacts_dir=artifacts_dir,
        valgrind_bin=valgrind_bin,
        max_artifact_bytes=max_artifact_bytes,
        max_artifact_preview_bytes=max_artifact_preview_bytes,
        r2_endpoint=r2_endpoint,
        r2_access_key_id=r2_access_key_id,
        r2_secret_access_key=r2_secret_access_key,
        r2_bucket=r2_bucket,
        r2_region=r2_region,
        r2_use_ssl=r2_use_ssl,
        r2_presign_expires_sec=r2_presign_expires_sec,
        r2_upload_prefix=r2_upload_prefix,
        r2_max_upload_bytes=r2_max_upload_bytes,
        r2_download_timeout_sec=r2_download_timeout_sec,
        r2_allow_hosts=r2_allow_hosts,
        r2_healthcheck_on_startup=r2_healthcheck_on_startup,
        r2_healthcheck_timeout_sec=r2_healthcheck_timeout_sec,
    )

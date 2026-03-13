from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

from mcp_dynamic_analysis_server.tools.analyze_memcheck import analyze_memcheck
from mcp_dynamic_analysis_server.tools.create_upload_url import create_upload_url


def _ensure_leak_binary(root: Path) -> Path:
    bin_path = root / "examples" / "vulnerable" / "bin" / "leak"
    if bin_path.exists():
        return bin_path
    subprocess.run(["make", "-C", str(root / "examples" / "vulnerable")], check=True)
    return bin_path


def _upload_via_presigned(url: str, file_path: Path, content_type: str) -> None:
    data = file_path.read_bytes()
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", content_type)
    req.add_header("Content-Length", str(len(data)))
    with urllib.request.urlopen(req, timeout=30) as resp:
        _ = resp.read()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("WORKSPACE_ROOT", str(root))
    os.environ.setdefault("RUNS_DIR", str(root / "runs"))
    os.environ.setdefault("ARTIFACTS_DIR", str(root / "artifacts"))

    leak_bin = _ensure_leak_binary(root)
    size = leak_bin.stat().st_size

    print("== Create R2 upload URL ==")
    upload = create_upload_url(
        {
            "filename": "leak.bin",
            "content_type": "application/octet-stream",
            "size_bytes": size,
        }
    )
    print(json.dumps(upload, indent=2))

    print("== Uploading to R2 ==")
    _upload_via_presigned(upload["upload_url"], leak_bin, "application/octet-stream")

    print("== Analyze via artifact_id ==")
    result = analyze_memcheck(
        {
            "artifact_id": upload["artifact_id"],
            "timeout_sec": 30,
            "track_origins": True,
            "leak_check": "full",
            "show_leak_kinds": "all",
            "xml": True,
        }
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

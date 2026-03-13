from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable, Optional

from .exceptions import ValidationError


def download_file(
    url: str,
    dest: Path,
    max_bytes: int,
    timeout_sec: int,
    expected_sha256: Optional[str] = None,
    allow_hosts: Optional[Iterable[str]] = None,
) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Only http/https URLs are allowed for download")
    if allow_hosts:
        if parsed.hostname not in set(allow_hosts):
            raise ValidationError("Download host not in allowlist")

    dest.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    total = 0

    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        with dest.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValidationError("Downloaded artifact exceeds size limit")
                sha256.update(chunk)
                handle.write(chunk)

    if expected_sha256:
        digest = sha256.hexdigest()
        if digest.lower() != expected_sha256.lower():
            raise ValidationError("SHA256 mismatch for downloaded artifact")

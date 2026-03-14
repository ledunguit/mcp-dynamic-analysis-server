from __future__ import annotations

import re
from typing import Any, Dict, List


_ERROR_PATTERNS = [
    re.compile(r"ERROR: AddressSanitizer: (?P<kind>.+)$"),
    re.compile(r"ERROR: LeakSanitizer: (?P<kind>.+)$"),
]

_FRAME_PATTERN = re.compile(
    r"#\d+\s+0x[0-9a-fA-F]+\s+in\s+(?P<func>[^ ]+)(?:\s+(?P<file>/[^:]+):(?P<line>\d+))?"
)


def parse_asan_log(text: str) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    lines = text.splitlines()
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        kind = _match_kind(line)
        if kind:
            message = line.strip()
            stack: List[Dict[str, Any]] = []
            idx += 1
            while idx < len(lines):
                current = lines[idx]
                if _match_kind(current):
                    break
                if current.lstrip().startswith("#"):
                    frame = _parse_frame(current)
                    if frame:
                        stack.append(frame)
                idx += 1
            errors.append(
                {
                    "kind": kind,
                    "message": message,
                    "stack": stack,
                    "aux": {},
                }
            )
            continue
        idx += 1

    return errors


def _match_kind(line: str) -> str | None:
    for pattern in _ERROR_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group("kind").strip()
    return None


def _parse_frame(line: str) -> Dict[str, Any] | None:
    match = _FRAME_PATTERN.search(line)
    if not match:
        return None
    return {
        "function": match.group("func"),
        "file": match.group("file"),
        "line": int(match.group("line")) if match.group("line") else None,
    }

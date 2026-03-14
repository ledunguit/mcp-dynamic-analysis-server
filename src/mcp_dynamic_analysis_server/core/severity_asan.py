from __future__ import annotations


def map_asan_severity(kind: str, message: str) -> tuple[str, str]:
    kind_lower = (kind or "").lower()
    message_lower = (message or "").lower()

    if "use-after-free" in kind_lower or "use-after-free" in message_lower:
        return "high", "high"
    if "buffer-overflow" in kind_lower or "buffer-overflow" in message_lower:
        return "high", "high"
    if "use-after-scope" in kind_lower:
        return "high", "high"
    if "leaks" in kind_lower or "leak" in message_lower or "leaksan" in kind_lower:
        return "medium", "medium"

    return "medium", "low"

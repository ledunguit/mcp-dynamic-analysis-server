from __future__ import annotations


def map_severity(kind: str, message: str) -> tuple[str, str]:
    kind_lower = (kind or "").lower()
    message_lower = (message or "").lower()

    if "invalidread" in kind_lower or "invalid read" in message_lower:
        return "high", "high"
    if "invalidwrite" in kind_lower or "invalid write" in message_lower:
        return "high", "high"
    if "useafterfree" in kind_lower or "use after free" in message_lower:
        return "high", "high"
    if "conditional" in message_lower and "uninitialised" in message_lower:
        return "medium", "medium"
    if "definitelylost" in kind_lower or "definitely lost" in message_lower:
        return "medium", "medium"
    if "possiblylost" in kind_lower or "possibly lost" in message_lower:
        return "low", "medium"

    return "medium", "low"

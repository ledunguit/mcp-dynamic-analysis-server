from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree


def _text(node: Optional[ElementTree.Element]) -> Optional[str]:
    if node is None:
        return None
    if node.text is None:
        return None
    return node.text.strip() or None


def _parse_stack(stack_node: Optional[ElementTree.Element]) -> List[Dict[str, Any]]:
    frames: List[Dict[str, Any]] = []
    if stack_node is None:
        return frames
    for frame in stack_node.findall("frame"):
        frames.append(
            {
                "function": _text(frame.find("fn")),
                "file": _text(frame.find("file")),
                "line": _safe_int(_text(frame.find("line"))),
            }
        )
    return frames


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_memcheck(xml_path: Path) -> List[Dict[str, Any]]:
    tree = ElementTree.parse(xml_path)
    root = tree.getroot()
    errors: List[Dict[str, Any]] = []

    for error in root.findall("error"):
        kind = _text(error.find("kind")) or "Unknown"
        message = _text(error.find("xwhat/text")) or _text(error.find("what")) or ""
        aux: Dict[str, Any] = {}

        addr = _text(error.find("addr"))
        if addr:
            aux["address"] = addr
        size = _text(error.find("size"))
        if size:
            aux["size"] = _safe_int(size) or size

        xwhat = error.find("xwhat")
        if xwhat is not None:
            leak = xwhat.find("leak")
            if leak is not None:
                aux["leak"] = {
                    "bytes": _safe_int(_text(leak.find("bytes"))),
                    "blocks": _safe_int(_text(leak.find("blocks"))),
                    "kind": _text(leak.find("kind")),
                }

        auxwhat = _text(error.find("auxwhat"))
        if auxwhat:
            aux["auxwhat"] = auxwhat

        stack = _parse_stack(error.find("stack"))
        origin_stack = _parse_stack(error.find("origin/stack"))

        errors.append(
            {
                "kind": kind,
                "message": message,
                "stack": stack,
                "origin_stack": origin_stack,
                "aux": aux,
            }
        )

    return errors

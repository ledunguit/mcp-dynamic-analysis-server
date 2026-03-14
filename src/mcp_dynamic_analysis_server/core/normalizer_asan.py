from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List

from ..models.findings import (
    Finding,
    FindingEvidence,
    FindingLocation,
    FindingStats,
    NormalizedReport,
    StackFrame,
)
from .severity_asan import map_asan_severity


def _signature_for(kind: str, message: str, top_frame: Dict[str, Any]) -> str:
    parts = [
        kind or "",
        message or "",
        str(top_frame.get("function") or ""),
        str(top_frame.get("file") or ""),
        str(top_frame.get("line") or ""),
    ]
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def normalize_asan(
    run_id: str,
    raw_errors: List[Dict[str, Any]],
    log_path: Path,
) -> NormalizedReport:
    findings: List[Finding] = []

    for idx, raw in enumerate(raw_errors, start=1):
        kind = raw.get("kind", "Unknown")
        message = raw.get("message") or kind
        stack_raw = raw.get("stack") or []
        top_frame = stack_raw[0] if stack_raw else {}
        severity, confidence = map_asan_severity(kind, message)
        signature = _signature_for(kind, message, top_frame)

        stack = [
            StackFrame(
                function=frame.get("function"),
                file=frame.get("file"),
                line=frame.get("line"),
            )
            for frame in stack_raw
        ]
        location = FindingLocation(
            file=top_frame.get("file"),
            line=top_frame.get("line"),
            function=top_frame.get("function"),
        )

        findings.append(
            Finding(
                finding_id=f"asan-{idx:04d}",
                tool="asan",
                kind=kind,
                severity=severity,
                confidence=confidence,
                message=message,
                location=location,
                stack=stack,
                aux=raw.get("aux") or {},
                origin={},
                evidence=FindingEvidence(
                    xml_path=None,
                    log_path=str(log_path),
                ),
                signature=signature,
            )
        )

    stats = _compute_stats(findings)
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return NormalizedReport(
        run_id=run_id,
        tool="asan",
        findings=findings,
        stats=stats,
        generated_at=generated_at,
    )


def _compute_stats(findings: List[Finding]) -> FindingStats:
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    low = sum(1 for f in findings if f.severity == "low")
    return FindingStats(
        finding_count=len(findings),
        high=high,
        medium=medium,
        low=low,
    )

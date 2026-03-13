from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List

from mcp_dynamic_analysis_server.tools.analyze_memcheck import analyze_memcheck
from mcp_dynamic_analysis_server.tools.get_report import get_report


def _ensure_examples_built(root: Path) -> None:
    bin_invalid = root / "examples" / "vulnerable" / "bin" / "invalid_read"
    bin_leak = root / "examples" / "vulnerable" / "bin" / "leak"
    if bin_invalid.exists() and bin_leak.exists():
        return
    subprocess.run(["make", "-C", str(root / "examples" / "vulnerable")], check=True)


def _summarize(findings: List[Dict]) -> str:
    if not findings:
        return "No findings detected."

    lines = []
    leak_findings = [f for f in findings if "leak" in f.get("kind", "").lower()]
    invalid_findings = [f for f in findings if "invalid" in f.get("kind", "").lower()]

    lines.append(f"Total findings: {len(findings)}")
    if leak_findings:
        lines.append(f"Leaks: {len(leak_findings)}")
    if invalid_findings:
        lines.append(f"Invalid reads/writes: {len(invalid_findings)}")

    for f in findings:
        loc = f.get("location", {})
        location_str = f"{loc.get('file', '?')}:{loc.get('line', '?')} ({loc.get('function', '?')})"
        lines.append(
            f"- [{f.get('severity')}] {f.get('kind')}: {f.get('message')} @ {location_str}"
        )

    return "\n".join(lines)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("WORKSPACE_ROOT", str(root))
    os.environ.setdefault("RUNS_DIR", str(root / "runs"))

    _ensure_examples_built(root)

    print("== Running Memcheck on leak binary ==")
    run = analyze_memcheck(
        {
            "target_path": str(root / "examples" / "vulnerable" / "bin" / "leak"),
            "args": [],
            "cwd": str(root / "examples" / "vulnerable"),
            "timeout_sec": 30,
            "track_origins": True,
            "leak_check": "full",
            "show_leak_kinds": "all",
            "xml": True,
            "suppressions": [],
            "env": {},
            "stdin": "",
            "labels": ["demo-llm"],
        }
    )

    run_id = run["run_id"]
    print(f"run_id: {run_id}")
    print(f"stats: {run['stats']}")

    report = get_report({"run_id": run_id})
    findings = report.get("findings", [])

    print("\n== Summary ==")
    print(_summarize(findings))


if __name__ == "__main__":
    main()

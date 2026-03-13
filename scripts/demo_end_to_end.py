from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mcp_dynamic_analysis_server.tools.analyze_memcheck import analyze_memcheck
from mcp_dynamic_analysis_server.tools.compare_runs import compare_runs
from mcp_dynamic_analysis_server.tools.get_report import get_report
from mcp_dynamic_analysis_server.tools.list_findings import list_findings


def _ensure_examples_built(root: Path) -> None:
    bin_invalid = root / "examples" / "vulnerable" / "bin" / "invalid_read"
    bin_leak = root / "examples" / "vulnerable" / "bin" / "leak"
    if bin_invalid.exists() and bin_leak.exists():
        return
    subprocess.run(["make", "-C", str(root / "examples" / "vulnerable")], check=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("WORKSPACE_ROOT", str(root))
    os.environ.setdefault("RUNS_DIR", str(root / "runs"))

    _ensure_examples_built(root)

    print("== Running Valgrind Memcheck on invalid_read ==")
    run1 = analyze_memcheck(
        {
            "target_path": str(root / "examples" / "vulnerable" / "bin" / "invalid_read"),
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
            "labels": ["demo"],
        }
    )
    print(f"run_id: {run1['run_id']}")
    print(f"stats: {run1['stats']}")

    print("\n== Running Valgrind Memcheck on leak ==")
    run2 = analyze_memcheck(
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
            "labels": ["demo"],
        }
    )
    print(f"run_id: {run2['run_id']}")
    print(f"stats: {run2['stats']}")

    print("\n== Fetching full report for run1 ==")
    report1 = get_report({"run_id": run1["run_id"]})
    print(f"findings: {len(report1.get('findings', []))}")

    print("\n== Listing high severity findings in run1 ==")
    findings = list_findings(
        {
            "run_id": run1["run_id"],
            "severity": "high",
            "limit": 10,
        }
    )
    print(f"count: {findings['count']}")

    print("\n== Comparing runs ==")
    comparison = compare_runs(
        {
            "base_run_id": run1["run_id"],
            "new_run_id": run2["run_id"],
        }
    )
    print(f"summary: {comparison['summary']}")

    print("\nArtifacts:")
    print(f"run1 dir: {run1['artifacts']['run_dir']}")
    print(f"run2 dir: {run2['artifacts']['run_dir']}")


if __name__ == "__main__":
    main()

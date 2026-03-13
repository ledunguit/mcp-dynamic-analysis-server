import json
from pathlib import Path

from mcp_dynamic_analysis_server.core.compare import compare_findings
from mcp_dynamic_analysis_server.models.findings import Finding


def test_compare_runs_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_normalized_report.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    base = [Finding.model_validate(item) for item in data["findings"]]

    new_data = json.loads(fixture.read_text(encoding="utf-8"))
    new_data["findings"] = new_data["findings"][:1]
    new = [Finding.model_validate(item) for item in new_data["findings"]]

    fixed, added, persistent = compare_findings(base, new)

    assert len(fixed) == 1
    assert len(added) == 0
    assert len(persistent) == 1

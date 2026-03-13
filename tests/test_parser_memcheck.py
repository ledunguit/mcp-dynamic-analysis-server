from pathlib import Path

from mcp_dynamic_analysis_server.core.parser_memcheck import parse_memcheck


def test_parse_memcheck_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_memcheck.xml"
    errors = parse_memcheck(fixture)

    assert len(errors) == 2
    assert errors[0]["kind"] == "InvalidRead"
    assert "Invalid read" in errors[0]["message"]
    assert errors[1]["kind"].startswith("Leak")

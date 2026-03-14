from pathlib import Path

from mcp_dynamic_analysis_server.core.parser_asan import parse_asan_log


def test_parse_asan_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_asan.log"
    errors = parse_asan_log(fixture.read_text(encoding="utf-8"))

    assert len(errors) == 1
    assert "heap-use-after-free" in errors[0]["kind"]
    assert errors[0]["stack"][0]["file"].endswith("invalid_read.c")

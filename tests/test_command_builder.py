from pathlib import Path

import pytest

from mcp_dynamic_analysis_server.core.command_builder import build_memcheck_command
from mcp_dynamic_analysis_server.core.exceptions import ValidationError


def test_build_memcheck_command(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    result = build_memcheck_command(
        valgrind_bin="valgrind",
        target_path=Path("/bin/echo"),
        run_dir=run_dir,
        args=["hello"],
        track_origins=True,
        leak_check="full",
        show_leak_kinds="all",
        suppressions=[],
        xml_enabled=True,
    )

    assert "--xml=yes" in result.command
    assert any(str(result.xml_path) in item for item in result.command)
    assert any(str(result.log_path) in item for item in result.command)
    assert result.command[-2:] == ["/bin/echo", "hello"]


def test_build_memcheck_requires_xml(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    with pytest.raises(ValidationError):
        build_memcheck_command(
            valgrind_bin="valgrind",
            target_path=Path("/bin/echo"),
            run_dir=run_dir,
            args=[],
            track_origins=True,
            leak_check="full",
            show_leak_kinds="all",
            suppressions=[],
            xml_enabled=False,
        )

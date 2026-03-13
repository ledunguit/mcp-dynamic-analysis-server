from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .exceptions import ValidationError


@dataclass(frozen=True)
class CommandBuildResult:
    command: List[str]
    xml_path: Path
    log_path: Path


def build_memcheck_command(
    valgrind_bin: str,
    target_path: Path,
    run_dir: Path,
    args: List[str],
    track_origins: bool,
    leak_check: str,
    show_leak_kinds: str,
    suppressions: List[Path],
    xml_enabled: bool,
) -> CommandBuildResult:
    if not xml_enabled:
        raise ValidationError("XML output must be enabled for Memcheck parsing")

    xml_path = run_dir / "valgrind.xml"
    log_path = run_dir / "valgrind.log"

    command: List[str] = [
        valgrind_bin,
        "--tool=memcheck",
        "--xml=yes",
        f"--xml-file={xml_path}",
        f"--log-file={log_path}",
        "--child-silent-after-fork=yes",
        "-q",
        f"--leak-check={leak_check}",
        f"--show-leak-kinds={show_leak_kinds}",
        f"--track-origins={'yes' if track_origins else 'no'}",
        "--error-exitcode=42",
    ]

    for suppression in suppressions:
        command.append(f"--suppressions={suppression}")

    command.append(str(target_path))
    command.extend(args)
    return CommandBuildResult(command=command, xml_path=xml_path, log_path=log_path)

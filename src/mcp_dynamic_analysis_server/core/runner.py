from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .exceptions import RunnerError


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    timed_out: bool
    duration_sec: float
    started_at: str
    finished_at: str


def ensure_valgrind_available(valgrind_bin: str) -> None:
    if shutil.which(valgrind_bin) is None:
        raise RunnerError(
            f"Valgrind binary '{valgrind_bin}' not found in PATH. Please install Valgrind."
        )


def run_command(
    command: list[str],
    cwd: Optional[Path],
    env: Dict[str, str],
    stdin: Optional[str],
    timeout_sec: int,
    stdout_path: Path,
    stderr_path: Path,
) -> ExecutionResult:
    start = time.time()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start))
    timed_out = False

    with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=env,
                input=stdin,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=timeout_sec,
                check=False,
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = -1
        except OSError as exc:
            raise RunnerError(f"Failed to execute command: {exc}") from exc

    end = time.time()
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end))
    return ExecutionResult(
        exit_code=exit_code,
        timed_out=timed_out,
        duration_sec=end - start,
        started_at=started_at,
        finished_at=finished_at,
    )

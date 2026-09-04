from __future__ import annotations

import os
import sys
import time
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import CapabilityScope


def launch_process(
    command: Union[List[str], str],
    cwd: Optional[Union[str, Path]] = None,
    timeout_seconds: float = 30.0,
    env: Optional[Dict[str, str]] = None,
    scope: Optional[CapabilityScope] = None,
) -> Dict[str, Any]:
    """Safely executes a host process within optional CapabilityScope limits."""
    if scope is not None:
        scope.assert_subprocess_allowed()
        if cwd is not None:
            scope.assert_path_allowed(cwd)

    if isinstance(command, str):
        cmd_args = shlex.split(command, posix=(sys.platform != "win32"))
    else:
        cmd_args = [str(arg) for arg in command]

    if not cmd_args:
        raise ValueError("Process command must contain at least one executable argument")

    resolved_cwd = str(Path(cwd).resolve()) if cwd is not None else None

    # Merge custom environment with parent environment
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)

    start_time = time.perf_counter()
    timed_out = False
    stdout_text = ""
    stderr_text = ""
    exit_code = 0

    try:
        proc = subprocess.run(
            cmd_args,
            cwd=resolved_cwd,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
            env=exec_env,
            encoding="utf-8",
            errors="replace",
        )
        exit_code = proc.returncode
        stdout_text = proc.stdout or ""
        stderr_text = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = -1
        stdout_text = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr_text = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "Process execution timed out")
    except Exception as exc:
        exit_code = 1
        stderr_text = str(exc)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "exit_code": exit_code,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
    }

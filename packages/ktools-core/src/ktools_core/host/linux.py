from __future__ import annotations

import os
import sys
import time
import shlex
import shutil
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .provider import HostCapability, HostPlatform, HostProvider


class LinuxHostProvider(HostProvider):
    """Linux & Omarchy workstation reference host provider."""

    def __init__(self) -> None:
        self._clipboard_fallback: str = ""

    @property
    def platform(self) -> HostPlatform:
        return HostPlatform.LINUX

    @property
    def name(self) -> str:
        return "LinuxHostProvider"

    def supported_capabilities(self) -> Tuple[HostCapability, ...]:
        return (
            HostCapability.PROCESS_LAUNCH,
            HostCapability.CLIPBOARD_SYNC,
            HostCapability.HOST_HEALTH,
            HostCapability.NOTIFICATIONS,
        )

    def get_health_metrics(self, target_path: Optional[str] = None) -> Dict[str, Any]:
        check_dir = str(Path(target_path).resolve()) if target_path else os.getcwd()
        total, used, free = 0, 0, 0
        try:
            total, used, free = shutil.disk_usage(check_dir)
        except Exception:
            pass

        percent_used = round((used / total) * 100, 2) if total > 0 else 0.0

        extra_metrics: Dict[str, Any] = {}
        # Parse /proc/loadavg on real Linux if accessible
        try:
            if os.path.exists("/proc/loadavg"):
                with open("/proc/loadavg", "r", encoding="utf-8") as f:
                    parts = f.read().strip().split()
                    if len(parts) >= 3:
                        extra_metrics["load_avg"] = [float(p) for p in parts[:3]]
        except Exception:
            pass

        return {
            "platform": "linux",
            "os_name": "Linux" if platform.system() == "Linux" else platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
            "disk": {
                "path": check_dir,
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "percent_used": percent_used,
            },
            "extra": extra_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute_process(
        self,
        command: Union[List[str], str],
        cwd: Optional[str] = None,
        timeout_seconds: float = 30.0,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if isinstance(command, str):
            cmd_args = shlex.split(command, posix=True)
        else:
            cmd_args = [str(arg) for arg in command]

        resolved_cwd = str(Path(cwd).resolve()) if cwd else None
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        start = time.perf_counter()
        timed_out = False
        exit_code = 0
        stdout_txt = ""
        stderr_txt = ""

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
            stdout_txt = proc.stdout or ""
            stderr_txt = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = -1
            stdout_txt = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr_txt = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "Timed out")
        except Exception as exc:
            exit_code = 1
            stderr_txt = str(exc)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "exit_code": exit_code,
            "stdout": stdout_txt,
            "stderr": stderr_txt,
            "timed_out": timed_out,
            "duration_ms": duration_ms,
        }

    def read_clipboard(self) -> str:
        if sys.platform.startswith("linux"):
            for cmd in (["wl-paste", "--no-newline"], ["xclip", "-selection", "clipboard", "-o"]):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if res.returncode == 0:
                        return res.stdout
                except Exception:
                    continue
        return self._clipboard_fallback

    def write_clipboard(self, text: str) -> None:
        self._clipboard_fallback = text
        if sys.platform.startswith("linux"):
            for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
                try:
                    subprocess.run(cmd, input=text, text=True, timeout=2)
                    return
                except Exception:
                    continue

    def send_notification(self, title: str, message: str, level: str = "info") -> bool:
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(["notify-send", title, message], timeout=2)
            except Exception:
                pass
        return True

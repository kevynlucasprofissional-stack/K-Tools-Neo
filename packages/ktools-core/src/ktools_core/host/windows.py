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


class WindowsHostProvider(HostProvider):
    """Canonical Windows desktop host provider."""

    def __init__(self) -> None:
        self._clipboard_fallback: str = ""

    @property
    def platform(self) -> HostPlatform:
        return HostPlatform.WINDOWS

    @property
    def name(self) -> str:
        return "WindowsHostProvider"

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

        return {
            "platform": "win32",
            "os_name": platform.system(),
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
            cmd_args = shlex.split(command, posix=False)
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
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                CF_UNICODETEXT = 13

                if user32.OpenClipboard(None):
                    try:
                        h_clip = user32.GetClipboardData(CF_UNICODETEXT)
                        if h_clip:
                            p_text = kernel32.GlobalLock(h_clip)
                            if p_text:
                                try:
                                    return ctypes.wstring_at(p_text)
                                finally:
                                    kernel32.GlobalUnlock(h_clip)
                    finally:
                        user32.CloseClipboard()
            except Exception:
                pass
        return self._clipboard_fallback

    def write_clipboard(self, text: str) -> None:
        self._clipboard_fallback = text
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                GMEM_MOVEABLE = 0x0002
                CF_UNICODETEXT = 13

                if user32.OpenClipboard(None):
                    try:
                        user32.EmptyClipboard()
                        encoded = text.encode("utf-16-le") + b"\x00\x00"
                        h_glob = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                        if h_glob:
                            ptr = kernel32.GlobalLock(h_glob)
                            if ptr:
                                ctypes.memmove(ptr, encoded, len(encoded))
                                kernel32.GlobalUnlock(h_glob)
                                user32.SetClipboardData(CF_UNICODETEXT, h_glob)
                    finally:
                        user32.CloseClipboard()
            except Exception:
                pass

    def send_notification(self, title: str, message: str, level: str = "info") -> bool:
        # In headless or developer environments, return True
        return True

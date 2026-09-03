import os
import subprocess
from pathlib import Path
from typing import Sequence

from ktools_core.diagnostics import record_subprocess

_FFMPEG_EXE: str | None = None
_FFPROBE_EXE: str | None = None


def get_ffmpeg_exe() -> str:
    global _FFMPEG_EXE
    if _FFMPEG_EXE:
        return _FFMPEG_EXE

    try:
        import imageio_ffmpeg
        _FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
        return _FFMPEG_EXE
    except ImportError:
        raise RuntimeError("imageio_ffmpeg is required to resolve FFmpeg but is not installed.")


def get_ffprobe_exe() -> str | None:
    global _FFPROBE_EXE
    if _FFPROBE_EXE:
        return _FFPROBE_EXE

    import shutil
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        _FFPROBE_EXE = system_ffprobe
        return _FFPROBE_EXE

    try:
        ffmpeg_path = Path(get_ffmpeg_exe())
        exe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
        candidate = ffmpeg_path.parent / exe_name
        if candidate.exists():
            _FFPROBE_EXE = str(candidate)
            return _FFPROBE_EXE
    except Exception:
        pass
    
    return None


def _subprocess_creationflags() -> int:
    if os.name == "nt":
        return subprocess.CREATE_NO_WINDOW
    return 0


def run_ffmpeg(args: Sequence[str]) -> subprocess.CompletedProcess:
    """Executes FFmpeg with M3 diagnostics integration."""
    exe = get_ffmpeg_exe()
    command = [exe, *map(str, args)]

    # We must use record_subprocess to fulfill M3 diagnostics rules.
    # Note: record_subprocess(cmd, creationflags, etc...)
    # We will pass kwargs correctly.
    
    # K-Tools core diagnostics `record_subprocess` signature:
    # def record_subprocess(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    
    return record_subprocess(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_subprocess_creationflags(),
    )


def run_ffprobe(args: Sequence[str]) -> subprocess.CompletedProcess | None:
    """Executes FFprobe with M3 diagnostics integration."""
    exe = get_ffprobe_exe()
    if not exe:
        return None
    command = [exe, *map(str, args)]

    return record_subprocess(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_subprocess_creationflags(),
    )

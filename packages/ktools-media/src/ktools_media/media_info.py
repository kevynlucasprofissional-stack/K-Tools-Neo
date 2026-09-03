from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .ffmpeg import run_ffprobe

def get_media_duration(path: Path) -> float:
    '''
    Returns the duration of the media file in seconds using ffprobe.
    Raises ValueError if the duration cannot be determined.
    '''
    probe = run_ffprobe(
        [
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ]
    )
    if probe is None:
        raise RuntimeError("ffprobe is not available to determine duration.")

    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {probe.stderr}")

    try:
        data = json.loads(probe.stdout)
        duration_str = data.get("format", {}).get("duration")
        if duration_str is None:
            raise ValueError("Duration not found in ffprobe output.")
        return float(duration_str)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise ValueError(f"Could not parse media duration: {exc}")

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def compress_video(
    input_path: Path,
    output_path: Path,
    crf: int = 28,
    preset: str = "medium",
) -> Path:
    '''
    Compresses a video file using FFmpeg libx264.
    '''
    if not input_path.exists():
        raise FileNotFoundError(f"Input video does not exist: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = output_path.with_name(f"{output_path.name}.{uuid4().hex}.tmp")

    cmd = [
        "-y",
        "-i", str(input_path),
        "-vcodec", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        str(tmp_out),
    ]

    try:
        res = run_ffmpeg(cmd)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with code {res.returncode}: {res.stderr}")
            
        os.replace(tmp_out, output_path)
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

    return output_path

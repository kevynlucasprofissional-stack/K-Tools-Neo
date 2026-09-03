from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def convert_audio(
    input_path: Path,
    output_path: Path,
    output_format: str,
    bitrate: str | None = None,
) -> Path:
    '''
    Converts an audio file to the target format/bitrate using ffmpeg.
    Uses atomic temp-file replace strategy.
    '''
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio does not exist: {input_path}")

    tmp_out = output_path.with_name(f"{output_path.name}.{uuid4().hex}.tmp")
    
    cmd = ["-y", "-i", str(input_path)]
    if bitrate and bitrate.lower() != "automático":
        cmd.extend(["-b:a", bitrate])
    cmd.append(str(tmp_out))

    try:
        res = run_ffmpeg(cmd)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with code {res.returncode}: {res.stderr}")
        # Atomic promote
        os.replace(tmp_out, output_path)
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

    return output_path

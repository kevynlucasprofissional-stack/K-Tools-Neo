from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from ..ffmpeg import run_ffmpeg
from ..media_info import get_media_duration


def split_audio(
    input_path: Path,
    output_dir: Path,
    parts: int,
    output_format: str | None = None,
) -> list[Path]:
    '''
    Splits an audio file into parts equal duration segments.
    '''
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio does not exist: {input_path}")
    if parts < 2:
        raise ValueError("Parts must be at least 2.")

    duration = get_media_duration(input_path)
    part_duration = duration / parts

    out_fmt = output_format.strip('.').lower() if output_format else input_path.suffix.strip('.').lower()
    
    outputs: list[Path] = []
    
    for i in range(1, parts + 1):
        start_time = (i - 1) * part_duration
        
        target_name = f"{input_path.stem}_part_{i:02d}_of_{parts:02d}.{out_fmt}"
        target_path = output_dir / target_name
        
        tmp_out = target_path.with_name(f"{target_path.name}.{uuid4().hex}.tmp")
        
        # Build ffmpeg command
        cmd = ["-y"]
        cmd.extend(["-ss", f"{start_time:.3f}"])
        cmd.extend(["-i", str(input_path)])
        
        # Do not supply duration for the last piece to catch any trailing bits
        if i < parts:
            cmd.extend(["-t", f"{part_duration:.3f}"])
            
        cmd.append(str(tmp_out))
        
        try:
            res = run_ffmpeg(cmd)
            if res.returncode != 0:
                raise RuntimeError(f"FFmpeg failed with code {res.returncode}: {res.stderr}")
                
            os.replace(tmp_out, target_path)
            outputs.append(target_path)
        finally:
            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass

    return outputs

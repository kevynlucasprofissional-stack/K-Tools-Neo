from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def deess_audio(
    input_path: Path,
    output_path: Path,
    intensity: float = 0.5,
    frequency: float = 0.5,
    noise_reduction: bool = False,
    output_format: str = "wav",
) -> Path:
    """
    Applies dynamic de-essing to attenuate harsh sibilant frequencies ("s", "x", "ch", "sh")
    and optional spectral noise reduction.
    Writes atomically via a temporary .tmp file.
    """
    if not (0.0 <= intensity <= 1.0):
        raise ValueError("intensity must be between 0.0 and 1.0")
    if not (0.0 <= frequency <= 1.0):
        raise ValueError("frequency must be between 0.0 and 1.0")

    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    out_fmt = output_format.strip(".").lower()
    final_output = output_path
    if final_output.suffix.strip(".").lower() != out_fmt:
        final_output = final_output.with_suffix(f".{out_fmt}")

    final_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = final_output.with_name(f"{final_output.name}.{uuid4().hex}.tmp")

    filter_chain: list[str] = [
        f"deesser=i={intensity:.2f}:m=0.5:f={frequency:.2f}:s=o"
    ]
    if noise_reduction:
        filter_chain.append("afftdn=nr=12:nf=-50")

    cmd = [
        "-y",
        "-i", str(input_path),
        "-vn", "-sn", "-dn",
        "-af", ",".join(filter_chain),
    ]

    if out_fmt == "wav":
        cmd.extend(["-c:a", "pcm_s16le"])
    elif out_fmt == "m4a":
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    elif out_fmt == "flac":
        cmd.extend(["-c:a", "flac"])
    elif out_fmt == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])

    cmd.append(str(tmp_out))

    try:
        res = run_ffmpeg(cmd)
        if res.returncode != 0 or not tmp_out.exists():
            raise RuntimeError(f"FFmpeg de-essing failed: {res.stderr}")

        os.replace(tmp_out, final_output)
        return final_output
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

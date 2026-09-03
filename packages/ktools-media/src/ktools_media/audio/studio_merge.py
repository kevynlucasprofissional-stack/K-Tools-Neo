from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Sequence
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def natural_sort_key(text: str) -> list[int | str]:
    """
    Splits string into numeric and non-numeric chunks so numbers are compared numerically.
    Example: 'track10.mp3' sorts after 'track2.mp3'.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text)]


def _escape_concat_line(path: Path) -> str:
    escaped = str(path.resolve()).replace("\\", "/").replace("'", "'\\''")
    return f"file '{escaped}'\n"


def merge_audio_studio(
    input_paths: Sequence[Path],
    output_path: Path,
    output_format: str = "m4a",
    bitrate: str = "192k",
    normalize_volume: bool = False,
    natural_sort: bool = True,
) -> tuple[Path, dict[str, Any]]:
    """
    Advanced audio merger supporting audio and video files.
    - Naturally sorts items.
    - Normalizes inputs to 44.1kHz 2-channel WAV (extracts audio from video).
    - Concatenates into target format (m4a, mp3, etc.).
    - Computes SHA-256 integrity hash of final file.
    - Writes atomically via a .tmp file.
    """
    if len(input_paths) < 2:
        raise ValueError("At least 2 audio/video files are required to merge.")

    files = [Path(p) for p in input_paths]
    for p in files:
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {p}")

    if natural_sort:
        files = sorted(files, key=lambda p: natural_sort_key(p.name))

    out_fmt = output_format.strip(".").lower()
    final_output = output_path
    if final_output.suffix.strip(".").lower() != out_fmt:
        final_output = final_output.with_suffix(f".{out_fmt}")

    final_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = final_output.with_name(f"{final_output.name}.{uuid4().hex}.tmp")

    with TemporaryDirectory(prefix="ktools_studio_merge_") as tmp_dir:
        temp_path = Path(tmp_dir)
        wav_paths: list[Path] = []

        # 1. Normalize each input to WAV (extracts audio from video cleanly)
        for i, src in enumerate(files):
            wav_file = temp_path / f"part_{i:04d}.wav"
            cmd_wav = [
                "-y",
                "-i", str(src),
                "-vn", "-sn", "-dn",
                "-ar", "44100",
                "-ac", "2",
                "-f", "wav",
                str(wav_file),
            ]
            res_wav = run_ffmpeg(cmd_wav)
            if res_wav.returncode != 0:
                raise RuntimeError(f"Failed to prepare audio from {src.name}: {res_wav.stderr}")
            wav_paths.append(wav_file)

        # 2. Concat demuxer script
        concat_txt = temp_path / "concat.txt"
        concat_txt.write_text("".join(_escape_concat_line(w) for w in wav_paths), encoding="utf-8")

        # 3. Final concat and encoding
        cmd_concat = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
        ]

        if normalize_volume:
            cmd_concat.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])

        if out_fmt == "m4a":
            cmd_concat.extend(["-c:a", "aac", "-b:a", bitrate, "-movflags", "+faststart"])
        elif out_fmt == "mp3":
            cmd_concat.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
        elif out_fmt == "wav":
            cmd_concat.extend(["-c:a", "pcm_s16le"])

        cmd_concat.append(str(tmp_out))

        res_concat = run_ffmpeg(cmd_concat)
        if res_concat.returncode != 0 or not tmp_out.exists():
            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"Studio audio merge failed: {res_concat.stderr}")

        # 4. Compute integrity SHA-256
        hasher = hashlib.sha256()
        with open(tmp_out, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        digest = hasher.hexdigest()

        os.replace(tmp_out, final_output)

        metadata: dict[str, Any] = {
            "name": final_output.name,
            "format": out_fmt,
            "size_bytes": final_output.stat().st_size,
            "sha256": digest,
            "item_count": len(files),
            "normalized_volume": normalize_volume,
        }

    return final_output, metadata

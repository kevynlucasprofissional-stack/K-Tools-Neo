from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def _escape_concat_path(path: Path) -> str:
    escaped = str(path.resolve()).replace("\\", "/").replace("'", "'\\''")
    return f"file '{escaped}'\n"


def join_videos(
    input_paths: Sequence[Path],
    output_path: Path,
    fast_copy: bool = True,
) -> Path:
    """
    Joins multiple video files into a single MP4 video using FFmpeg.
    First tries fast stream-copy concat. If that fails (e.g. codec/resolution mismatch),
    falls back to normalizing all videos to standard H.264/AAC and concatenating them.
    """
    if len(input_paths) < 2:
        raise ValueError("At least 2 video files are required to join.")

    files = [Path(p) for p in input_paths]
    for p in files:
        if not p.exists():
            raise FileNotFoundError(f"Input video not found: {p}")

    final_output = output_path
    if final_output.suffix.lower() != ".mp4":
        final_output = final_output.with_suffix(".mp4")

    final_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = final_output.with_name(f"{final_output.name}.{uuid4().hex}.tmp")

    with TemporaryDirectory(prefix="ktools_video_join_") as tmp_dir:
        temp_path = Path(tmp_dir)

        # 1. Fast copy attempt
        if fast_copy:
            concat_list = temp_path / "concat_fast.txt"
            concat_list.write_text("".join(_escape_concat_path(p) for p in files), encoding="utf-8")

            res_fast = run_ffmpeg([
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                "-movflags", "+faststart",
                str(tmp_out),
            ])

            if res_fast.returncode == 0 and tmp_out.exists() and tmp_out.stat().st_size > 0:
                os.replace(tmp_out, final_output)
                return final_output

            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass

        # 2. Fallback normalization route
        normalized: list[Path] = []
        for index, src in enumerate(files, start=1):
            temp_video = temp_path / f"video_{index:04d}.mp4"
            res_norm = run_ffmpeg([
                "-y",
                "-i", str(src),
                "-map", "0:v:0",
                "-map", "0:a?",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(temp_video),
            ])

            if res_norm.returncode != 0 or not temp_video.exists():
                raise RuntimeError(f"Failed to normalize video: {src.name}")
            normalized.append(temp_video)

        concat_normalized = temp_path / "concat_normalized.txt"
        concat_normalized.write_text("".join(_escape_concat_path(p) for p in normalized), encoding="utf-8")

        res_final = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_normalized),
            "-c", "copy",
            "-movflags", "+faststart",
            str(tmp_out),
        ])

        if res_final.returncode != 0 or not tmp_out.exists() or tmp_out.stat().st_size == 0:
            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"Failed to concatenate videos: {res_final.stderr}")

        os.replace(tmp_out, final_output)

    return final_output

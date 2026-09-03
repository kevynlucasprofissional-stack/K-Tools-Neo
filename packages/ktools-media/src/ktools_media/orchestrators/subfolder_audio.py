from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from ..audio.studio_merge import merge_audio_studio, natural_sort_key
from ..ffmpeg import run_ffmpeg

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".m4v", ".ts"
}


def extract_and_join_by_subfolder(
    root_dir: Path,
    output_dir: Optional[Path] = None,
    output_format: str = "m4a",
    bitrate: str = "192k",
) -> tuple[list[Path], dict[str, Any]]:
    """
    Recursively scans root_dir for video files, groups them by parent folder,
    and for each subfolder produces a single merged audio track.
    Returns the list of generated audio files and an execution report.
    """
    root_path = Path(root_dir)
    if not root_path.exists() or not root_path.is_dir():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")

    # Group videos by parent folder
    folder_videos: dict[Path, list[Path]] = defaultdict(list)
    total_videos = 0

    for current_root, _, files in os.walk(root_path):
        cur_dir = Path(current_root)
        for f in files:
            p = cur_dir / f
            if p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                folder_videos[cur_dir].append(p)
                total_videos += 1

    if output_dir is not None:
        out_root = Path(output_dir)
        out_root.mkdir(parents=True, exist_ok=True)
    else:
        out_root = None

    out_fmt = output_format.strip(".").lower()
    generated_audios: list[Path] = []
    folder_summaries: list[dict[str, Any]] = []

    # Process each subfolder
    for folder_path, vids in sorted(folder_videos.items(), key=lambda item: natural_sort_key(item[0].name)):
        sorted_vids = sorted(vids, key=lambda p: natural_sort_key(p.name))

        folder_name = folder_path.name if folder_path != root_path else "root_audio"
        dest_dir = out_root if out_root is not None else folder_path
        dest_path = dest_dir / f"{folder_name}.{out_fmt}"

        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{folder_name}_{counter}.{out_fmt}"
            counter += 1

        if len(sorted_vids) == 1:
            # Single video: extract audio directly
            from uuid import uuid4
            tmp_out = dest_path.with_name(f"{dest_path.name}.{uuid4().hex}.tmp")
            cmd = [
                "-y",
                "-i", str(sorted_vids[0]),
                "-vn", "-sn", "-dn",
                "-c:a", "aac" if out_fmt == "m4a" else ("libmp3lame" if out_fmt == "mp3" else "pcm_s16le"),
                "-b:a", bitrate,
                str(tmp_out),
            ]
            res = run_ffmpeg(cmd)
            if res.returncode == 0 and tmp_out.exists():
                os.replace(tmp_out, dest_path)
                generated_audios.append(dest_path)
                folder_summaries.append({
                    "folder": str(folder_path),
                    "video_count": 1,
                    "output_audio": str(dest_path),
                })
            else:
                if tmp_out.exists():
                    try:
                        tmp_out.unlink()
                    except OSError:
                        pass
        else:
            # Multiple videos: merge audio studio
            final_audio, meta = merge_audio_studio(
                input_paths=sorted_vids,
                output_path=dest_path,
                output_format=out_fmt,
                bitrate=bitrate,
                natural_sort=False,  # already sorted
            )
            generated_audios.append(final_audio)
            folder_summaries.append({
                "folder": str(folder_path),
                "video_count": len(sorted_vids),
                "output_audio": str(final_audio),
                "sha256": meta.get("sha256"),
            })

    report = {
        "root_dir": str(root_path),
        "total_folders_processed": len(folder_summaries),
        "total_videos_processed": total_videos,
        "folders": folder_summaries,
    }

    return generated_audios, report

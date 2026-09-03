import os
import re
from pathlib import Path
from typing import Any

from ktools_core.models import Artifact, DataType
from ktools_core.registry import NodeExecutionContext

from ..ffmpeg import run_ffmpeg, run_ffprobe


class MediaExtractionError(Exception):
    pass


def media_has_audio_stream(path: Path) -> bool:
    probe = run_ffprobe(
        [
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    if probe is not None:
        if probe.returncode != 0:
            return False
        return bool(probe.stdout and probe.stdout.strip())
        
    result = run_ffmpeg(["-i", str(path)])
    output = f"{result.stderr or ''}\n{result.stdout or ''}"
    return bool(re.search(r"Stream #\d+:\d+.*Audio:", output, flags=re.IGNORECASE))


def audio_codec_args(format_ext: str, bitrate: str | None = None) -> list[str]:
    ext = format_ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    bitrate_arg = ["-b:a", bitrate] if bitrate and bitrate.lower() != "auto" else []

    if ext == ".mp3":
        if not bitrate_arg:
            bitrate_arg = ["-q:a", "2"] # VBR fallback
        return ["-c:a", "libmp3lame"] + bitrate_arg
    if ext in {".m4a", ".aac"}:
        if not bitrate_arg:
            bitrate_arg = ["-b:a", "192k"]
        return ["-c:a", "aac"] + bitrate_arg
    if ext == ".wav":
        return ["-c:a", "pcm_s16le"]
    if ext == ".flac":
        return ["-c:a", "flac"]
    
    # Fallback default
    if not bitrate_arg:
        bitrate_arg = ["-b:a", "192k"]
    return ["-c:a", "aac"] + bitrate_arg


def temp_output_path_for(path: Path) -> Path:
    return path.with_name(f"{path.stem}.ktools_tmp{path.suffix}")


def _mime_type_for_ext(ext: str) -> str:
    ext = ext.lower()
    if ext == ".mp3":
        return "audio/mpeg"
    if ext in {".m4a", ".aac"}:
        return "audio/mp4"
    if ext == ".wav":
        return "audio/wav"
    if ext == ".flac":
        return "audio/flac"
    return "audio/mpeg"


def extract_audio_from_video(
    video_path: Path,
    output_path: Path,
    format: str = "m4a",
    bitrate: str | None = None,
    context: NodeExecutionContext | None = None,
) -> Artifact:
    video_path = video_path.expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    if not media_has_audio_stream(video_path):
        raise MediaExtractionError(f"Video does not have a detectable audio stream: {video_path}")

    ext = format.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    
    # Ensure correct extension on output path
    output_path = output_path.expanduser().resolve()
    if output_path.suffix.lower() != ext:
        output_path = output_path.with_suffix(ext)

    if output_path == video_path:
        raise MediaExtractionError("Output path cannot be the same as input path")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_out = temp_output_path_for(output_path)
    
    codec_args = audio_codec_args(ext, bitrate)
    
    try:
        result = run_ffmpeg(
            [
                "-y",
                "-i",
                str(video_path),
                "-vn",
                *codec_args,
                str(temp_out),
            ]
        )
        
        if result.returncode != 0:
            raise MediaExtractionError(f"FFmpeg failed with exit code {result.returncode}")
        
        os.replace(temp_out, output_path)
    finally:
        if temp_out.exists():
            try:
                temp_out.unlink()
            except OSError:
                pass

    produced_by = None
    if context:
        produced_by = f"{context.run_id}/{context.node_id}"

    metadata = {
        "name": output_path.name,
        "size": output_path.stat().st_size,
    }

    return Artifact.create(
        type=DataType.AUDIO,
        uri=output_path.as_uri(),
        produced_by=produced_by,
        mime_type=_mime_type_for_ext(ext),
        metadata=metadata,
    )

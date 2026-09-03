from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .audio.extract import extract_audio_from_video


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id="media.extract_audio",
            title="Extract Audio",
            category="Media",
            inputs={
                "video": PortDefinition(DataType.FILE),
            },
            outputs={
                "audio": PortDefinition(DataType.AUDIO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _extract_audio_node,
    )


def _extract_audio_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    video_artifact = inputs["video"]
    if video_artifact.type not in (DataType.FILE, DataType.VIDEO):
        raise TypeError("media.extract_audio requires a FILE or VIDEO artifact")

    video_path = path_from_file_uri(video_artifact.uri)

    # Determine output path
    # If not provided in config, use the video path's directory with a new suffix
    format_ext = config.get("format", "m4a")
    bitrate = config.get("bitrate")
    
    ext = format_ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    output_dir = video_path.parent
    output_path = output_dir / f"{video_path.stem}_audio{ext}"
    
    # Simple collision handling if we don't have output path specified
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{video_path.stem}_audio_{counter}{ext}"
        counter += 1

    audio_artifact = extract_audio_from_video(
        video_path=video_path,
        output_path=output_path,
        format=format_ext,
        bitrate=bitrate,
        context=context,
    )

    return {"audio": audio_artifact}

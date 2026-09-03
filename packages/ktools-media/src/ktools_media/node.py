from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .audio.extract import extract_audio_from_video
from .audio.convert import convert_audio
from .audio.split import split_audio


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
    registry.register(
        NodeDefinition(
            type_id="media.split_audio",
            title="Split Audio",
            category="Media",
            inputs={
                "audio": PortDefinition(DataType.FILE),
            },
            outputs={
                "pieces": PortDefinition(DataType.FILE_SET),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _split_audio_node,
    )
    registry.register(
        NodeDefinition(
            type_id="media.convert_audio",
            title="Convert Audio",
            category="Media",
            inputs={
                "audio": PortDefinition(DataType.FILE),
                
            },
            outputs={
                "audio": PortDefinition(DataType.AUDIO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _convert_audio_node,
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

def _convert_audio_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    audio_artifact = inputs["audio"]
    if audio_artifact.type not in (DataType.FILE, DataType.AUDIO):
        raise TypeError("media.convert_audio requires an AUDIO or FILE artifact")

    input_path = path_from_file_uri(audio_artifact.uri)
    out_format = config.get("format", "m4a").lower().strip(".")
    bitrate = config.get("bitrate")

    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    output_path = output_dir / f"{input_path.stem}.{out_format}"

    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_{counter}.{out_format}"
        counter += 1

    final_path = convert_audio(
        input_path=input_path,
        output_path=output_path,
        output_format=out_format,
        bitrate=bitrate,
    )

    
    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.AUDIO,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "format": out_format,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"audio": out_artifact}

def _split_audio_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    audio_artifact = inputs["audio"]
    if audio_artifact.type not in (DataType.FILE, DataType.AUDIO):
        raise TypeError("media.split_audio requires an AUDIO or FILE artifact")

    input_path = path_from_file_uri(audio_artifact.uri)
    
    parts = config.get("parts")
    if not isinstance(parts, int) or parts < 2:
        raise ValueError("media.split_audio config 'parts' must be an integer >= 2")

    out_format = config.get("format")
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    pieces_paths = split_audio(
        input_path=input_path,
        output_dir=output_dir,
        parts=parts,
        output_format=out_format,
    )

    from ktools_core.models import Artifact
    
    pieces_artifacts = []
    for p_path in pieces_paths:
        pieces_artifacts.append(
            Artifact.create(
                type=DataType.AUDIO,
                uri=p_path.as_uri(),
                metadata={
                    "name": p_path.name,
                    "format": p_path.suffix.strip("."),
                    "size_bytes": p_path.stat().st_size,
                },
            )
        )
        
    return {"pieces": pieces_artifacts}

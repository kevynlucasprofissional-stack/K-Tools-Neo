from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .audio.extract import extract_audio_from_video
from .audio.convert import convert_audio
from .audio.split import split_audio
from .audio.join import join_audios
from .video.compress import compress_video
from .video.join import join_videos
from .image.webp_to_png import webp_to_png
from .pdf.merge import merge_pdfs
from .pdf.split import split_pdf


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
            type_id="media.compress_video",
            title="Compress Video",
            category="Media",
            inputs={
                "video": PortDefinition(DataType.FILE),
            },
            outputs={
                "video": PortDefinition(DataType.VIDEO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _compress_video_node,
    )
    registry.register(
        NodeDefinition(
            type_id="media.join_videos",
            title="Join Videos",
            category="Media",
            inputs={
                "videos": PortDefinition(DataType.FILE_SET),
            },
            outputs={
                "video": PortDefinition(DataType.VIDEO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _join_videos_node,
    )
    registry.register(
        NodeDefinition(
            type_id="media.join_audios",
            title="Join Audios",
            category="Media",
            inputs={
                "audios": PortDefinition(DataType.FILE_SET),
            },
            outputs={
                "audio": PortDefinition(DataType.AUDIO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _join_audios_node,
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
    registry.register(
        NodeDefinition(
            type_id="media.webp_to_png",
            title="WebP to PNG",
            category="Media",
            inputs={
                "image": PortDefinition(DataType.FILE),
            },
            outputs={
                "image": PortDefinition(DataType.IMAGE),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _webp_to_png_node,
    )
    registry.register(
        NodeDefinition(
            type_id="pdf.merge",
            title="Merge PDFs",
            category="PDF",
            inputs={
                "pdfs": PortDefinition(DataType.FILE_SET),
            },
            outputs={
                "pdf": PortDefinition(DataType.FILE),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _merge_pdfs_node,
    )
    registry.register(
        NodeDefinition(
            type_id="pdf.split",
            title="Split PDF",
            category="PDF",
            inputs={
                "pdf": PortDefinition(DataType.FILE),
            },
            outputs={
                "parts": PortDefinition(DataType.FILE_SET),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _split_pdf_node,
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


def _join_audios_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    # audios could be a single FILE_SET artifact or a list of Artifacts
    audios = inputs.get("audios")
    if not audios:
        raise ValueError("media.join_audios requires 'audios' input.")
        
    artifacts = audios if isinstance(audios, list) else [audios]
    
    # We might need to handle if a FILE_SET artifact is passed with no payload vs list of files.
    # We assume 'audios' is a list of Artifact instances generated by a split or scan node.
    if len(artifacts) < 2:
        raise ValueError("media.join_audios requires at least 2 audio files in the set.")
        
    # Sort to ensure determinism
    artifacts = sorted(artifacts, key=lambda a: a.metadata.get("name", a.uri) if a.metadata else a.uri)
    
    input_paths = [path_from_file_uri(a.uri) for a in artifacts]
    
    out_format = config.get("format", "m4a").lower().strip(".")
    bitrate = config.get("bitrate")
    
    output_dir = input_paths[0].parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        
    output_path = output_dir / f"joined_audio.{out_format}"
    
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"joined_audio_{counter}.{out_format}"
        counter += 1
        
    final_path = join_audios(
        input_paths=input_paths,
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


def _compress_video_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    video_artifact = inputs["video"]
    if video_artifact.type not in (DataType.FILE, DataType.VIDEO):
        raise TypeError("media.compress_video requires a VIDEO or FILE artifact")

    input_path = path_from_file_uri(video_artifact.uri)
    
    crf = config.get("crf", 28)
    preset = config.get("preset", "medium")
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        
    output_path = output_dir / f"{input_path.stem}_compressed{input_path.suffix}"
    
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_compressed_{counter}{input_path.suffix}"
        counter += 1
        
    final_path = compress_video(
        input_path=input_path,
        output_path=output_path,
        crf=int(crf),
        preset=str(preset),
    )
    
    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.VIDEO,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"video": out_artifact}


def _webp_to_png_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    image_artifact = inputs["image"]
    if image_artifact.type not in (DataType.FILE, DataType.IMAGE):
        raise TypeError("media.webp_to_png requires an IMAGE or FILE artifact")

    input_path = path_from_file_uri(image_artifact.uri)
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        
    output_path = output_dir / f"{input_path.stem}.png"
    
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_{counter}.png"
        counter += 1
        
    final_path = webp_to_png(
        input_path=input_path,
        output_path=output_path,
    )
    
    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.IMAGE,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "format": "png",
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"image": out_artifact}


def _merge_pdfs_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    pdfs = inputs.get("pdfs")
    if not pdfs:
        raise ValueError("pdf.merge requires 'pdfs' input.")

    artifacts = pdfs if isinstance(pdfs, list) else [pdfs]
    artifacts = sorted(artifacts, key=lambda a: a.metadata.get("name", a.uri) if a.metadata else a.uri)

    input_paths = [path_from_file_uri(a.uri) for a in artifacts]

    output_dir = input_paths[0].parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    output_name = config.get("output_name", "merged.pdf")
    output_path = output_dir / output_name

    counter = 1
    while output_path.exists():
        output_path = output_dir / f"merged_{counter}.pdf"
        counter += 1

    final_path = merge_pdfs(
        input_paths=input_paths,
        output_path=output_path,
    )

    from ktools_core.models import Artifact

    out_artifact = Artifact.create(
        type=DataType.FILE,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"pdf": out_artifact}


def _split_pdf_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    pdf_artifact = inputs["pdf"]
    if pdf_artifact.type not in (DataType.FILE,):
        raise TypeError("pdf.split requires a FILE artifact")

    input_path = path_from_file_uri(pdf_artifact.uri)

    parts = config.get("parts")
    if not isinstance(parts, int) or parts < 2:
        raise ValueError("pdf.split config 'parts' must be an integer >= 2")

    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    part_paths = split_pdf(
        input_path=input_path,
        output_dir=output_dir,
        parts=parts,
    )

    from ktools_core.models import Artifact

    part_artifacts = []
    for p_path in part_paths:
        part_artifacts.append(
            Artifact.create(
                type=DataType.FILE,
                uri=p_path.as_uri(),
                metadata={
                    "name": p_path.name,
                    "size_bytes": p_path.stat().st_size,
                },
            )
        )

    return {"parts": part_artifacts}


def _join_videos_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    videos = inputs.get("videos")
    if not videos:
        raise ValueError("media.join_videos requires 'videos' input.")

    artifacts = videos if isinstance(videos, list) else [videos]
    if len(artifacts) < 2:
        raise ValueError("media.join_videos requires at least 2 video files.")

    artifacts = sorted(artifacts, key=lambda a: a.metadata.get("name", a.uri) if a.metadata else a.uri)
    input_paths = [path_from_file_uri(a.uri) for a in artifacts]

    output_dir = input_paths[0].parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    output_name = config.get("output_name", "joined_video.mp4")
    output_path = output_dir / output_name

    counter = 1
    while output_path.exists():
        output_path = output_dir / f"joined_video_{counter}.mp4"
        counter += 1

    fast_copy = config.get("fast_copy", True)

    final_path = join_videos(
        input_paths=input_paths,
        output_path=output_path,
        fast_copy=fast_copy,
    )

    from ktools_core.models import Artifact

    out_artifact = Artifact.create(
        type=DataType.VIDEO,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "format": "mp4",
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"video": out_artifact}

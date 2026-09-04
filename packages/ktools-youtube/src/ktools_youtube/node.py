from __future__ import annotations

from typing import Any, Mapping

from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .engine.service import YouTubeDownloadService


def register_nodes(registry: NodeRegistry) -> None:
    node_def = NodeDefinition(
        type_id="youtube.download",
        title="Baixar do YouTube",
        category="Download",
        inputs={
            "url": PortDefinition(DataType.TEXT, required=False),
            "media_type": PortDefinition(DataType.TEXT, required=False),
            "quality": PortDefinition(DataType.TEXT, required=False),
            "audio_format": PortDefinition(DataType.TEXT, required=False),
            "output_dir": PortDefinition(DataType.FOLDER, required=False),
            "use_auth": PortDefinition(DataType.BOOLEAN, required=False),
        },
        outputs={
            "files": PortDefinition(DataType.FILE_SET),
            "folder": PortDefinition(DataType.FOLDER),
            "metadata": PortDefinition(DataType.JSON),
        },
        version="1",
        cache_policy=CachePolicy.NEVER,
    )
    registry.register(node_def, _youtube_download_node)


def _youtube_download_node(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    url = inputs.get("url") or config.get("url")
    if not url:
        raise ValueError("A URL do vídeo ou playlist do YouTube é obrigatória.")

    media_type = inputs.get("media_type") or config.get("media_type") or "video"
    quality = inputs.get("quality") or config.get("quality") or "best"
    audio_format = inputs.get("audio_format") or config.get("audio_format") or "m4a"
    output_dir = inputs.get("output_dir") or config.get("output_dir")
    use_auth = inputs.get("use_auth") if "use_auth" in inputs else config.get("use_auth")

    service = YouTubeDownloadService()
    res = service.download(
        url=str(url).strip(),
        media_type=str(media_type).strip(),
        quality=str(quality).strip(),
        audio_format=str(audio_format).strip(),
        output_dir=output_dir,
        use_auth=use_auth,
    )

    return {
        "files": res.files,
        "folder": res.folder,
        "metadata": res.metadata,
    }

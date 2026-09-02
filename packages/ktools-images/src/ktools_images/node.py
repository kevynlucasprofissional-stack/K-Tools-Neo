from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import LocalFileUriError, path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from . import converter
from .converter import ImageConversionError

WEBP_TO_PNG_NODE_TYPE_ID = "image.webp_to_png"


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id=WEBP_TO_PNG_NODE_TYPE_ID,
            title="WebP para PNG",
            category="Images",
            inputs={"files": PortDefinition(DataType.FILE_SET)},
            outputs={"files": PortDefinition(DataType.FILE_SET)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _webp_to_png_handler,
    )


def _artifact_path(artifact: Artifact) -> Path:
    if artifact.type not in {DataType.FILE, DataType.IMAGE}:
        raise ImageConversionError(
            f"{WEBP_TO_PNG_NODE_TYPE_ID} requires FILE/IMAGE Artifacts, got {artifact.type.value}"
        )
    try:
        return path_from_file_uri(artifact.uri)
    except LocalFileUriError as exc:
        raise ImageConversionError(
            f"{WEBP_TO_PNG_NODE_TYPE_ID} received an unsupported Artifact URI: {exc}"
        ) from exc


def _webp_to_png_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    raw_files = inputs.get("files")
    if not isinstance(raw_files, (list, tuple)) or not raw_files:
        raise ImageConversionError(
            f"{WEBP_TO_PNG_NODE_TYPE_ID} requires a non-empty ordered FILE_SET"
        )

    paths: list[Path] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, Artifact):
            raise ImageConversionError(
                f"{WEBP_TO_PNG_NODE_TYPE_ID} files[{index}] must be an Artifact"
            )
        paths.append(_artifact_path(item))

    output_dir = config.get("output_dir")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ImageConversionError(
            f"{WEBP_TO_PNG_NODE_TYPE_ID} config.output_dir is required"
        )

    outputs = converter.convert_webp_files_to_png(
        paths,
        Path(output_dir),
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"files": outputs}

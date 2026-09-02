from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import LocalFileUriError, path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from . import converter, pdf_writer
from .converter import ImageConversionError
from .pdf_writer import ImagePdfError

WEBP_TO_PNG_NODE_TYPE_ID = "image.webp_to_png"
IMAGES_TO_PDF_NODE_TYPE_ID = "image.files_to_pdf"


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
    registry.register(
        NodeDefinition(
            type_id=IMAGES_TO_PDF_NODE_TYPE_ID,
            title="Imagens para PDF",
            category="Images",
            inputs={"files": PortDefinition(DataType.FILE_SET)},
            outputs={"pdf": PortDefinition(DataType.PDF)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _images_to_pdf_handler,
    )


def _artifact_path(
    artifact: Artifact,
    *,
    node_type_id: str,
    error_type: type[RuntimeError],
) -> Path:
    if artifact.type not in {DataType.FILE, DataType.IMAGE}:
        raise error_type(
            f"{node_type_id} requires FILE/IMAGE Artifacts, got {artifact.type.value}"
        )
    try:
        return path_from_file_uri(artifact.uri)
    except LocalFileUriError as exc:
        raise error_type(
            f"{node_type_id} received an unsupported Artifact URI: {exc}"
        ) from exc


def _ordered_artifact_paths(
    inputs: dict[str, Any],
    *,
    node_type_id: str,
    error_type: type[RuntimeError],
) -> list[Path]:
    raw_files = inputs.get("files")
    if not isinstance(raw_files, (list, tuple)) or not raw_files:
        raise error_type(f"{node_type_id} requires a non-empty ordered FILE_SET")

    paths: list[Path] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, Artifact):
            raise error_type(f"{node_type_id} files[{index}] must be an Artifact")
        paths.append(
            _artifact_path(
                item,
                node_type_id=node_type_id,
                error_type=error_type,
            )
        )
    return paths


def _webp_to_png_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    paths = _ordered_artifact_paths(
        inputs,
        node_type_id=WEBP_TO_PNG_NODE_TYPE_ID,
        error_type=ImageConversionError,
    )

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


def _images_to_pdf_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    paths = _ordered_artifact_paths(
        inputs,
        node_type_id=IMAGES_TO_PDF_NODE_TYPE_ID,
        error_type=ImagePdfError,
    )

    output_file = config.get("output_file")
    if not isinstance(output_file, str) or not output_file.strip():
        raise ImagePdfError(
            f"{IMAGES_TO_PDF_NODE_TYPE_ID} config.output_file is required"
        )

    artifact = pdf_writer.images_to_pdf(
        paths,
        Path(output_file),
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"pdf": artifact}

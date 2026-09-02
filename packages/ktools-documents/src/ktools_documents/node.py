from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import LocalFileUriError, path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from . import batch
from .batch import DocumentSplitBatchError

DOCUMENT_SPLIT_NODE_TYPE_ID = "document.split.files"


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id=DOCUMENT_SPLIT_NODE_TYPE_ID,
            title="Dividir documentos",
            category="Documents",
            inputs={"files": PortDefinition(DataType.FILE_SET)},
            outputs={
                "files": PortDefinition(DataType.FILE_SET),
                "report": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _split_documents_handler,
    )


def _artifact_path(artifact: Artifact) -> Path:
    if artifact.type not in {DataType.FILE, DataType.PDF}:
        raise DocumentSplitBatchError(
            f"{DOCUMENT_SPLIT_NODE_TYPE_ID} requires FILE/PDF Artifacts, got {artifact.type.value}"
        )
    try:
        return path_from_file_uri(artifact.uri)
    except LocalFileUriError as exc:
        raise DocumentSplitBatchError(
            f"{DOCUMENT_SPLIT_NODE_TYPE_ID} received an unsupported Artifact URI: {exc}"
        ) from exc


def _split_documents_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    raw_files = inputs.get("files")
    if not isinstance(raw_files, (list, tuple)) or not raw_files:
        raise DocumentSplitBatchError(
            f"{DOCUMENT_SPLIT_NODE_TYPE_ID} requires a non-empty ordered FILE_SET"
        )

    artifacts: list[Artifact] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, Artifact):
            raise DocumentSplitBatchError(
                f"{DOCUMENT_SPLIT_NODE_TYPE_ID} files[{index}] must be an Artifact"
            )
        artifacts.append(item)

    output_dir = config.get("output_dir")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise DocumentSplitBatchError(
            f"{DOCUMENT_SPLIT_NODE_TYPE_ID} config.output_dir is required"
        )
    parts = config.get("parts")

    result = batch.split_documents_into_parts(
        [_artifact_path(artifact) for artifact in artifacts],
        Path(output_dir),
        parts,
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"files": list(result.artifacts), "report": result.to_report()}

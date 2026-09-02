from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import LocalFileUriError, path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from . import writer
from .capability import TextMergeError

NODE_TYPE_ID = "text.merge.files"


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id=NODE_TYPE_ID,
            title="Juntar Markdown/TXT",
            category="Text",
            inputs={"files": PortDefinition(DataType.FILE_SET)},
            outputs={"file": PortDefinition(DataType.FILE)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _merge_files_handler,
    )


def _artifact_path(artifact: Artifact) -> Path:
    if artifact.type is not DataType.FILE:
        raise TextMergeError(
            f"text.merge.files requires FILE Artifacts, got {artifact.type.value}"
        )
    try:
        return path_from_file_uri(artifact.uri)
    except LocalFileUriError as exc:
        raise TextMergeError(f"text.merge.files received an unsupported Artifact URI: {exc}") from exc


def _merge_files_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    raw_files = inputs.get("files")
    if not isinstance(raw_files, (list, tuple)) or not raw_files:
        raise TextMergeError("text.merge.files requires a non-empty ordered FILE_SET")
    artifacts: list[Artifact] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, Artifact):
            raise TextMergeError(
                f"text.merge.files files[{index}] must be an Artifact"
            )
        artifacts.append(item)

    output_path = config.get("output_path")
    if not isinstance(output_path, str) or not output_path.strip():
        raise TextMergeError("text.merge.files config.output_path is required")
    separator_mode = config.get("separator_mode", "completo")
    if not isinstance(separator_mode, str):
        raise TextMergeError("text.merge.files config.separator_mode must be a string")

    output = writer.merge_text_files(
        [_artifact_path(artifact) for artifact in artifacts],
        Path(output_path),
        separator_mode,
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"file": output}

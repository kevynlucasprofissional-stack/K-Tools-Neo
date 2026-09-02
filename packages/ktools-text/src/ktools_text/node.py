from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .capability import TextMergeError
from . import writer

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
    parsed = urlparse(artifact.uri)
    if parsed.scheme.lower() != "file":
        raise TextMergeError("text.merge.files supports only local file:// Artifacts")
    if parsed.netloc not in {"", "localhost"}:
        raise TextMergeError("text.merge.files does not support UNC/network file URIs in V1")
    raw_path = url2pathname(unquote(parsed.path))
    if os.name == "nt" and len(raw_path) >= 3 and raw_path[0] in {"/", "\\"} and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return Path(raw_path).resolve()


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

from __future__ import annotations

from pathlib import Path
from typing import Any

from ktools_core.local_files import LocalFileUriError, path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from . import splitter, writer
from .capability import TextMergeError
from .splitter import TextSplitError
from .tldv import extract_tldv_transcript, export_transcript_outputs

NODE_TYPE_ID = "text.merge.files"
SPLIT_NODE_TYPE_ID = "text.split.parts"
TLDV_NODE_TYPE_ID = "text.tldv_extract"


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
    registry.register(
        NodeDefinition(
            type_id=SPLIT_NODE_TYPE_ID,
            title="Dividir Markdown/TXT",
            category="Text",
            inputs={"file": PortDefinition(DataType.FILE)},
            outputs={"files": PortDefinition(DataType.FILE_SET)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _split_parts_handler,
    )
    registry.register(
        NodeDefinition(
            type_id=TLDV_NODE_TYPE_ID,
            title="Extrair Transcrição tl;dv",
            category="Text",
            inputs={"html": PortDefinition(DataType.FILE)},
            outputs={
                "markdown": PortDefinition(DataType.FILE),
                "srt": PortDefinition(DataType.FILE),
                "json": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _tldv_extract_handler,
    )


def _artifact_path(artifact: Artifact, operation: str) -> Path:
    if artifact.type is not DataType.FILE:
        raise ValueError(f"{operation} requires a FILE Artifact, got {artifact.type.value}")
    try:
        return path_from_file_uri(artifact.uri)
    except LocalFileUriError as exc:
        raise ValueError(f"{operation} received an unsupported Artifact URI: {exc}") from exc


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

    try:
        input_paths = [_artifact_path(artifact, NODE_TYPE_ID) for artifact in artifacts]
    except ValueError as exc:
        raise TextMergeError(str(exc)) from exc

    output = writer.merge_text_files(
        input_paths,
        Path(output_path),
        separator_mode,
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"file": output}


def _split_parts_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    artifact = inputs.get("file")
    if not isinstance(artifact, Artifact):
        raise TextSplitError("text.split.parts requires one FILE Artifact")
    output_dir = config.get("output_dir")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise TextSplitError("text.split.parts config.output_dir is required")
    parts = config.get("parts")
    try:
        source_path = _artifact_path(artifact, SPLIT_NODE_TYPE_ID)
    except ValueError as exc:
        raise TextSplitError(str(exc)) from exc

    outputs = splitter.split_text_file_into_parts(
        source_path,
        Path(output_dir),
        parts,
        produced_by=f"{context.run_id}/{context.node_id}",
    )
    return {"files": outputs}


def _tldv_extract_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    artifact = inputs.get("html")
    if not isinstance(artifact, Artifact) or artifact.type != DataType.FILE:
        raise ValueError("text.tldv_extract requires an html FILE Artifact")

    html_path = _artifact_path(artifact, TLDV_NODE_TYPE_ID)
    html_content = html_path.read_text(encoding="utf-8", errors="replace")

    blocks = extract_tldv_transcript(html_content)

    output_dir = html_path.parent
    if "output_dir" in config and config["output_dir"]:
        output_dir = Path(config["output_dir"])

    title = config.get("title")
    md_path, srt_path, json_payload = export_transcript_outputs(
        blocks=blocks,
        output_dir=output_dir,
        base_name=html_path.stem,
        title=title,
    )

    md_artifact = Artifact.create(
        type=DataType.FILE,
        uri=md_path.as_uri(),
        metadata={
            "name": md_path.name,
            "format": "markdown",
            "size_bytes": md_path.stat().st_size,
        },
    )
    srt_artifact = Artifact.create(
        type=DataType.FILE,
        uri=srt_path.as_uri(),
        metadata={
            "name": srt_path.name,
            "format": "srt",
            "size_bytes": srt_path.stat().st_size,
        },
    )
    json_artifact = Artifact.create(
        type=DataType.JSON,
        uri=html_path.as_uri(),
        metadata=json_payload,
    )

    return {
        "markdown": md_artifact,
        "srt": srt_artifact,
        "json": json_artifact,
    }

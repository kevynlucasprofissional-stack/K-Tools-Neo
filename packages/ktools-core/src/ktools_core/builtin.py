from __future__ import annotations

from numbers import Real
from pathlib import Path
from typing import Any

from .models import Artifact, CachePolicy, DataType, NodeDefinition, PortDefinition
from .registry import NodeExecutionContext, NodeRegistry


def register_builtin_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id="text.literal",
            title="Texto",
            category="Text",
            outputs={"text": PortDefinition(DataType.TEXT)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _text_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="text.concat",
            title="Concatenar texto",
            category="Text",
            inputs={
                "left": PortDefinition(DataType.TEXT),
                "right": PortDefinition(DataType.TEXT),
            },
            outputs={"text": PortDefinition(DataType.TEXT)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _text_concat,
    )
    registry.register(
        NodeDefinition(
            type_id="number.literal",
            title="Número",
            category="Core",
            outputs={"number": PortDefinition(DataType.NUMBER)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _number_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="file.literal",
            title="Arquivo",
            category="Files",
            outputs={"file": PortDefinition(DataType.FILE)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _file_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="folder.literal",
            title="Pasta",
            category="Files",
            outputs={"folder": PortDefinition(DataType.FOLDER)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _folder_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="files.literal",
            title="Arquivos",
            category="Files",
            outputs={"files": PortDefinition(DataType.FILE_SET)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _files_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="core.identity",
            title="Identity",
            category="Core",
            inputs={"value": PortDefinition(DataType.ANY)},
            outputs={"value": PortDefinition(DataType.ANY)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _identity,
    )
    registry.register(
        NodeDefinition(
            type_id="core.literal",
            title="Literal",
            category="Core",
            outputs={"value": PortDefinition(DataType.ANY)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _core_literal,
    )


def _core_literal(
    _inputs: dict[str, Any], config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    return {"value": config.get("value")}



def _text_literal(
    _inputs: dict[str, Any], config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    value = config.get("value", "")
    if not isinstance(value, str):
        raise TypeError("text.literal config.value must be a string")
    return {"text": value}


def _text_concat(
    inputs: dict[str, Any], config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    separator = config.get("separator", "")
    if not isinstance(separator, str):
        raise TypeError("text.concat config.separator must be a string")
    left = inputs["left"]
    right = inputs["right"]
    if not isinstance(left, str) or not isinstance(right, str):
        raise TypeError("text.concat requires string inputs")
    return {"text": f"{left}{separator}{right}"}


def _number_literal(
    _inputs: dict[str, Any], config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    value = config.get("value")
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("number.literal config.value must be numeric")
    return {"number": value}


def _local_file_artifact(
    raw_path: Any,
    context: NodeExecutionContext,
    *,
    config_label: str,
    source_index: int | None = None,
) -> Artifact:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise TypeError(f"{config_label} must be a non-empty string")
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"local file path does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"local file path is not a file: {path}")
    metadata: dict[str, Any] = {"name": path.name}
    if source_index is not None:
        metadata["sourceIndex"] = source_index
    return Artifact.create(
        type=DataType.FILE,
        uri=path.as_uri(),
        produced_by=f"{context.run_id}/{context.node_id}",
        metadata=metadata,
    )


def _file_literal(
    _inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    artifact = _local_file_artifact(
        config.get("path"),
        context,
        config_label="file.literal config.path",
    )
    return {"file": artifact}


def _folder_literal(
    _inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    raw_path = config.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise TypeError("folder.literal config.path must be a non-empty string")
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"local folder path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"local folder path is not a directory: {path}")
    metadata = {"name": path.name}
    artifact = Artifact.create(
        type=DataType.FOLDER,
        uri=path.as_uri(),
        produced_by=f"{context.run_id}/{context.node_id}",
        metadata=metadata,
    )
    return {"folder": artifact}


def _files_literal(
    _inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    raw_paths = config.get("paths")
    if not isinstance(raw_paths, (list, tuple)) or not raw_paths:
        raise TypeError("files.literal config.paths must be a non-empty list of local file paths")

    artifacts = [
        _local_file_artifact(
            raw_path,
            context,
            config_label=f"files.literal config.paths[{index}]",
            source_index=index,
        )
        for index, raw_path in enumerate(raw_paths)
    ]
    return {"files": artifacts}


def _identity(
    inputs: dict[str, Any], _config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    return {"value": inputs["value"]}

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


def _files_literal(
    _inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    raw_paths = config.get("paths")
    if not isinstance(raw_paths, (list, tuple)) or not raw_paths:
        raise TypeError("files.literal config.paths must be a non-empty list of local file paths")

    artifacts: list[Artifact] = []
    for index, raw_path in enumerate(raw_paths):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise TypeError(f"files.literal config.paths[{index}] must be a non-empty string")
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"files.literal path does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"files.literal path is not a file: {path}")
        artifacts.append(
            Artifact.create(
                type=DataType.FILE,
                uri=path.as_uri(),
                produced_by=f"{context.run_id}/{context.node_id}",
                metadata={"name": path.name, "sourceIndex": index},
            )
        )
    return {"files": artifacts}


def _identity(
    inputs: dict[str, Any], _config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    return {"value": inputs["value"]}

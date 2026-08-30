from __future__ import annotations

from numbers import Real
from typing import Any

from .models import DataType, NodeDefinition, PortDefinition
from .registry import NodeExecutionContext, NodeRegistry


def register_builtin_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id="text.literal",
            title="Texto",
            category="Text",
            outputs={"text": PortDefinition(DataType.TEXT)},
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
        ),
        _text_concat,
    )
    registry.register(
        NodeDefinition(
            type_id="number.literal",
            title="Número",
            category="Core",
            outputs={"number": PortDefinition(DataType.NUMBER)},
        ),
        _number_literal,
    )
    registry.register(
        NodeDefinition(
            type_id="core.identity",
            title="Identity",
            category="Core",
            inputs={"value": PortDefinition(DataType.ANY)},
            outputs={"value": PortDefinition(DataType.ANY)},
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


def _identity(
    inputs: dict[str, Any], _config: dict[str, Any], _context: NodeExecutionContext
) -> dict[str, Any]:
    return {"value": inputs["value"]}

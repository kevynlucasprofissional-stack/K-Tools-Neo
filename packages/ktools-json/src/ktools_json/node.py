"""Workflow node adapters for the JSON split capability (OC-001).

All split semantics remain owned by :mod:`ktools_json.capability`. ``json.split``
publishes files and is intentionally side-effectful/non-cacheable. The
``json.split.plan`` adapter exposes the same deterministic transformation without
I/O so workflows can reuse/cache expensive planning independently from file
publication.
"""

from __future__ import annotations

from typing import Any

from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .capability import JsonSplitError, make_options, split_json_document
from .writer import DEFAULT_PREFIX, split_and_write

NODE_TYPE_ID = "json.split"
PLAN_TYPE_ID = "json.split.plan"
LITERAL_TYPE_ID = "json.literal"


def register_nodes(registry: NodeRegistry) -> None:
    """Register the JSON node pack into ``registry``."""
    registry.register(
        NodeDefinition(
            type_id=NODE_TYPE_ID,
            title="Dividir JSON",
            category="JSON",
            inputs={"json_data": PortDefinition(DataType.JSON)},
            outputs={
                "parts": PortDefinition(DataType.JSON),
                "summary": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _json_split_handler,
    )
    registry.register(
        NodeDefinition(
            type_id=PLAN_TYPE_ID,
            title="Planejar divisão JSON",
            category="JSON",
            inputs={"json_data": PortDefinition(DataType.JSON)},
            outputs={"plan": PortDefinition(DataType.JSON)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _json_split_plan_handler,
    )
    registry.register(
        NodeDefinition(
            type_id=LITERAL_TYPE_ID,
            title="JSON literal",
            category="JSON",
            outputs={"json": PortDefinition(DataType.JSON)},
            version="1",
            cache_policy=CachePolicy.PURE,
        ),
        _json_literal_handler,
    )


def build_options(config: dict[str, Any]) -> Any:
    """Build validated split options from node config (helper exposed for reuse)."""
    return make_options(
        mode=config.get("mode", "parts"),
        parts=config.get("parts"),
        target_bytes=config.get("target_bytes"),
    )


def _plan_payload(data: Any, config: dict[str, Any]) -> dict[str, Any]:
    plan = split_json_document(data, build_options(config))
    return {
        "rootType": plan.root_type,
        "listPath": plan.list_path_label,
        "itemCount": plan.item_count,
        "partCount": plan.part_count,
        "chunks": list(plan.chunks),
        "estimatedSizes": list(plan.estimated_sizes),
    }


def _json_split_plan_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    _context: NodeExecutionContext,
) -> dict[str, Any]:
    return {"plan": _plan_payload(inputs["json_data"], config)}


def _json_split_handler(
    inputs: dict[str, Any],
    config: dict[str, Any],
    _context: NodeExecutionContext,
) -> dict[str, Any]:
    data = inputs["json_data"]

    output_dir = config.get("output_dir")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise JsonSplitError("json.split config.output_dir is required")

    prefix = config.get("prefix", DEFAULT_PREFIX)
    if not isinstance(prefix, str) or not prefix.strip():
        raise JsonSplitError("json.split config.prefix must be a non-empty string")

    overwrite = config.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise JsonSplitError("json.split config.overwrite must be a boolean")

    options = build_options(config)
    result = split_and_write(
        data, options, output_dir, prefix=prefix, overwrite=overwrite
    )
    return {
        "parts": [part.to_dict() for part in result.parts],
        "summary": dict(result.summary),
    }


def _json_literal_handler(
    _inputs: dict[str, Any],
    config: dict[str, Any],
    _context: NodeExecutionContext,
) -> dict[str, Any]:
    """Fixture-quality JSON source node enabling typed JSON composition."""
    value = config.get("value")
    if not isinstance(value, (dict, list)):
        raise JsonSplitError("json.literal config.value must be a JSON object or array")
    return {"json": value}

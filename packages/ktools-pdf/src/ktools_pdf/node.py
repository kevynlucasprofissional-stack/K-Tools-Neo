from __future__ import annotations

from typing import Any

from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

NODE_TYPE_ID = "pdf.merge.files"


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id=NODE_TYPE_ID,
            title="Juntar PDFs",
            category="PDF",
            inputs={"files": PortDefinition(DataType.FILE_SET)},
            outputs={"pdf": PortDefinition(DataType.PDF)},
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _merge_files_handler,
    )


def _merge_files_handler(
    _inputs: dict[str, Any],
    _config: dict[str, Any],
    _context: NodeExecutionContext,
) -> dict[str, Any]:
    raise NotImplementedError("RED: pdf.merge.files handler not implemented yet")

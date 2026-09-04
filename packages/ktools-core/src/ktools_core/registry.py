from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .models import NodeDefinition


@dataclass(frozen=True)
class NodeExecutionContext:
    run_id: str
    workflow_id: str
    node_id: str


NodeHandler = Callable[[dict[str, Any], dict[str, Any], NodeExecutionContext], dict[str, Any]]


class NodeRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, NodeDefinition] = {}
        self._handlers: dict[str, NodeHandler] = {}

    def register(self, definition: NodeDefinition, handler: NodeHandler) -> None:
        if definition.type_id in self._definitions:
            raise ValueError(f"Node type already registered: {definition.type_id}")
        self._definitions[definition.type_id] = definition
        self._handlers[definition.type_id] = handler

    @property
    def definitions(self) -> dict[str, NodeDefinition]:
        return dict(self._definitions)

    def definition(self, type_id: str) -> NodeDefinition:
        try:
            return self._definitions[type_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node type: {type_id}") from exc

    def execute(
        self,
        type_id: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        try:
            handler = self._handlers[type_id]
        except KeyError as exc:
            raise KeyError(f"Unknown node type: {type_id}") from exc
        return handler(inputs, config, context)

    def type_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))


def load_all_installed_node_packs(registry: NodeRegistry | None = None) -> NodeRegistry:
    from .builtin import register_builtin_nodes

    reg = registry or NodeRegistry()
    register_builtin_nodes(reg)

    known_packs = (
        "ktools_json.node",
        "ktools_text.node",
        "ktools_pdf.node",
        "ktools_documents.node",
        "ktools_images.node",
        "ktools_filesystem.node",
        "ktools_media.node",
        "ktools_system.node",
        "ktools_script.node",
        "ktools_youtube.node",
    )
    for mod_name in known_packs:
        try:
            mod = __import__(mod_name, fromlist=["register_nodes"])
            if hasattr(mod, "register_nodes"):
                mod.register_nodes(reg)
        except ImportError:
            pass

    return reg

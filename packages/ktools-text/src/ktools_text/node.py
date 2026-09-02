from __future__ import annotations

from ktools_core.registry import NodeRegistry

NODE_TYPE_ID = "text.merge.files"


def register_nodes(registry: NodeRegistry) -> None:
    del registry
    # RED: registration is added after characterization tests prove the contract.

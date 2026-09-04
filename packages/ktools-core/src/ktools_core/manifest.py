from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from ktools_core.registry import NodeRegistry
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition


class SideEffectClass(str, Enum):
    PURE = "pure"
    READ_ONLY = "read_only"
    IDEMPOTENT_MUTATION = "idempotent_mutation"
    DESTRUCTIVE_MUTATION = "destructive_mutation"
    UNCONSTRAINED = "unconstrained"


@dataclass
class PortSpec:
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    default: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "data_type": self.data_type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            d["default"] = self.default
        return d


@dataclass
class CapabilityDefinition:
    capability_id: str
    version: str = "1.0.0"
    title: str = ""
    description: str = ""
    category: str = "General"
    inputs: Dict[str, PortSpec] = field(default_factory=dict)
    outputs: Dict[str, PortSpec] = field(default_factory=dict)
    side_effect_class: SideEffectClass = SideEffectClass.IDEMPOTENT_MUTATION
    cache_policy: str = "conservative"
    network_required: bool = False
    privilege_elevation: bool = False
    supports_dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "inputs": {k: v.to_dict() for k, v in self.inputs.items()},
            "outputs": {k: v.to_dict() for k, v in self.outputs.items()},
            "side_effect_class": self.side_effect_class.value,
            "cache_policy": self.cache_policy,
            "network_required": self.network_required,
            "privilege_elevation": self.privilege_elevation,
            "supports_dry_run": self.supports_dry_run,
        }


@dataclass
class CapabilityManifest:
    version: str = "1.0.0"
    capabilities: Dict[str, CapabilityDefinition] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _infer_side_effect(category: str, type_id: str, cache_policy: CachePolicy) -> SideEffectClass:
    cat = category.lower()
    tid = type_id.lower()
    if cat in ("core", "math") or "identity" in tid or "literal" in tid:
        return SideEffectClass.PURE
    if "scan" in tid or "report" in tid or cat == "diagnostics":
        return SideEffectClass.READ_ONLY
    if "delete" in tid or "remove" in tid:
        return SideEffectClass.DESTRUCTIVE_MUTATION
    return SideEffectClass.IDEMPOTENT_MUTATION


def generate_capability_manifest(registry: NodeRegistry, version: str = "1.0.0") -> CapabilityManifest:
    manifest = CapabilityManifest(version=version)

    for type_id, node_def in registry.definitions.items():
        inputs = {}
        for p_name, port in node_def.inputs.items():
            inputs[p_name] = PortSpec(
                name=p_name,
                data_type=port.type.value,
                required=port.required,
                description=getattr(port, "description", "") or "",
            )

        outputs = {}
        for p_name, port in node_def.outputs.items():
            outputs[p_name] = PortSpec(
                name=p_name,
                data_type=port.type.value,
                required=port.required,
                description=getattr(port, "description", "") or "",
            )

        side_effect = _infer_side_effect(node_def.category, type_id, node_def.cache_policy)

        cap_def = CapabilityDefinition(
            capability_id=type_id,
            version=getattr(node_def, "version", "1.0.0"),
            title=node_def.title or type_id,
            description=getattr(node_def, "description", "") or "",
            category=node_def.category or "General",
            inputs=inputs,
            outputs=outputs,
            side_effect_class=side_effect,
            cache_policy=node_def.cache_policy.value,
            network_required=False,
            privilege_elevation=False,
            supports_dry_run=(side_effect in (SideEffectClass.PURE, SideEffectClass.READ_ONLY)),
        )
        manifest.capabilities[type_id] = cap_def

    return manifest

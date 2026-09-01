from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class DataType(str, Enum):
    ANY = "any"
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    URL = "url"
    FILE = "file"
    FOLDER = "folder"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    PDF = "pdf"
    EVENT = "event"


class CachePolicy(str, Enum):
    """Whether a node may be skipped through semantic cache reuse.

    NEVER is intentionally the default. A node becomes PURE only when the
    capability owner explicitly claims deterministic outputs for equivalent
    semantic inputs/config and no externally required side effects.
    """

    NEVER = "never"
    PURE = "pure"


_FILE_SUBTYPES = {DataType.AUDIO, DataType.VIDEO, DataType.IMAGE, DataType.PDF}


def is_type_compatible(source: DataType, target: DataType) -> bool:
    if target is DataType.ANY:
        return True
    if source == target:
        return True
    return source in _FILE_SUBTYPES and target is DataType.FILE


@dataclass(frozen=True)
class PortDefinition:
    type: DataType
    required: bool = True


@dataclass(frozen=True)
class NodeDefinition:
    type_id: str
    title: str
    inputs: Mapping[str, PortDefinition] = field(default_factory=dict)
    outputs: Mapping[str, PortDefinition] = field(default_factory=dict)
    category: str = "Core"
    version: str = "1"
    cache_policy: CachePolicy = CachePolicy.NEVER


@dataclass(frozen=True)
class WorkflowNode:
    id: str
    type: str
    config: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkflowNode":
        return cls(id=str(raw["id"]), type=str(raw["type"]), config=dict(raw.get("config", {})))


@dataclass(frozen=True)
class WorkflowEdge:
    source_node: str
    source_port: str
    target_node: str
    target_port: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkflowEdge":
        return cls(
            source_node=str(raw["sourceNode"]),
            source_port=str(raw["sourcePort"]),
            target_node=str(raw["targetNode"]),
            target_port=str(raw["targetPort"]),
        )


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    nodes: tuple[WorkflowNode, ...]
    edges: tuple[WorkflowEdge, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkflowDefinition":
        return cls(
            id=str(raw.get("id", "workflow")),
            nodes=tuple(WorkflowNode.from_dict(node) for node in raw.get("nodes", [])),
            edges=tuple(WorkflowEdge.from_dict(edge) for edge in raw.get("edges", [])),
        )


@dataclass(frozen=True)
class Artifact:
    id: str
    type: DataType
    uri: str
    produced_by: str | None = None
    mime_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        type: DataType,
        uri: str,
        produced_by: str | None = None,
        mime_type: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Artifact":
        return cls(
            id=f"artifact_{uuid4().hex}",
            type=type,
            uri=uri,
            produced_by=produced_by,
            mime_type=mime_type,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "uri": self.uri,
            "producedBy": self.produced_by,
            "mimeType": self.mime_type,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Artifact":
        return cls(
            id=str(raw["id"]),
            type=DataType(str(raw["type"])),
            uri=str(raw["uri"]),
            produced_by=raw.get("producedBy"),
            mime_type=raw.get("mimeType"),
            metadata=dict(raw.get("metadata", {})),
        )

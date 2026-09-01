from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .models import Artifact


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


class NodeRunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


class RunEventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    NODE_STARTED = "NODE_STARTED"
    NODE_SUCCEEDED = "NODE_SUCCEEDED"
    NODE_FAILED = "NODE_FAILED"
    RUN_SUCCEEDED = "RUN_SUCCEEDED"
    RUN_FAILED = "RUN_FAILED"
    NODE_INTERRUPTED = "NODE_INTERRUPTED"
    RUN_INTERRUPTED = "RUN_INTERRUPTED"


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp suitable for durable records."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _qualified_type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def to_json_safe(value: Any) -> Any:
    """Convert runtime metadata to deterministic, JSON-safe structures.

    The converter has a deliberately small allow-list. Unknown objects are
    represented by type metadata only instead of inspecting attributes,
    dataclass fields or ``repr(value)``. This avoids journaling opaque object
    internals or credentials merely because a node returned a custom object.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            label = "NaN"
        elif value > 0:
            label = "Infinity"
        else:
            label = "-Infinity"
        return {"__type__": "float", "value": label}

    if isinstance(value, Enum):
        return to_json_safe(value.value)

    # Artifact is an explicit K-Tools persistence contract and is therefore
    # allowed to expose its documented serialization.
    if isinstance(value, Artifact):
        return to_json_safe(value.to_dict())

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, bytes):
        return {
            "__type__": "bytes",
            "sizeBytes": len(value),
            "__nonSerializable__": True,
        }

    if isinstance(value, Mapping):
        return {
            str(key): to_json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }

    if isinstance(value, (list, tuple)):
        return [to_json_safe(item) for item in value]

    if isinstance(value, (set, frozenset)):
        normalized = [to_json_safe(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    return {
        "__type__": _qualified_type_name(value),
        "__nonSerializable__": True,
    }


@dataclass(frozen=True)
class RunEvent:
    event_id: str
    run_id: str
    workflow_id: str
    event_type: RunEventType
    occurred_at: str
    node_id: str | None = None
    node_type: str | None = None
    payload: Mapping[str, Any] | None = None

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        workflow_id: str,
        event_type: RunEventType,
        node_id: str | None = None,
        node_type: str | None = None,
        payload: Mapping[str, Any] | None = None,
        occurred_at: str | None = None,
    ) -> "RunEvent":
        normalized = to_json_safe(dict(payload or {}))
        if not isinstance(normalized, dict):
            raise TypeError("RunEvent payload must normalize to a JSON object")
        return cls(
            event_id=f"event_{uuid4().hex}",
            run_id=run_id,
            workflow_id=workflow_id,
            event_type=event_type,
            occurred_at=occurred_at or utc_now_iso(),
            node_id=node_id,
            node_type=node_type,
            payload=normalized,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "eventId": self.event_id,
            "runId": self.run_id,
            "workflowId": self.workflow_id,
            "eventType": self.event_type.value,
            "occurredAt": self.occurred_at,
            "nodeId": self.node_id,
            "nodeType": self.node_type,
            "payload": dict(self.payload or {}),
        }


class RunJournal(Protocol):
    def record(self, event: RunEvent) -> None:
        """Persist or retain one ordered logical execution event."""


class NullRunJournal:
    """No-op journal used when callers do not request execution observability."""

    def record(self, event: RunEvent) -> None:
        del event


class MemoryRunJournal:
    """Simple ordered journal for tests and ephemeral/headless consumers."""

    def __init__(self) -> None:
        self._events: list[RunEvent] = []

    def record(self, event: RunEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[RunEvent, ...]:
        return tuple(self._events)

    def events_for_run(self, run_id: str) -> tuple[RunEvent, ...]:
        return tuple(event for event in self._events if event.run_id == run_id)

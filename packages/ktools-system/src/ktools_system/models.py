from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone


class PolicyAction(str, Enum):
    ALLOW = "allow"
    CONSTRAIN = "constrain"
    REQUIRE_HUMAN_CONFIRMATION = "require_human_confirmation"
    DENY = "deny"


class ScopeViolationError(PermissionError):
    """Raised when an operation violates caller CapabilityScope."""
    pass


@dataclass
class CapabilityScope:
    allowed_roots: List[Path] = field(default_factory=list)
    allow_subprocess: bool = True
    allow_network: bool = True
    allow_destructive: bool = False
    require_elevation: bool = False

    def is_path_allowed(self, path: Path | str) -> bool:
        if not self.allowed_roots:
            return True
        resolved = Path(path).resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False

    def assert_path_allowed(self, path: Path | str) -> None:
        if not self.is_path_allowed(path):
            raise ScopeViolationError(f"Access to path '{path}' is denied by CapabilityScope allowed_roots")

    def assert_subprocess_allowed(self) -> None:
        if not self.allow_subprocess:
            raise ScopeViolationError("Subprocess execution is denied by CapabilityScope allow_subprocess=False")

    def classify_action(self, side_effect_class: str) -> PolicyAction:
        sec = side_effect_class.lower()
        if sec in ("pure", "read_only"):
            return PolicyAction.ALLOW
        if sec == "idempotent_mutation":
            return PolicyAction.ALLOW if not self.require_elevation else PolicyAction.REQUIRE_HUMAN_CONFIRMATION
        if sec == "destructive_mutation":
            return PolicyAction.ALLOW if self.allow_destructive else PolicyAction.REQUIRE_HUMAN_CONFIRMATION
        return PolicyAction.REQUIRE_HUMAN_CONFIRMATION


@dataclass
class SystemEvent:
    event_type: str
    message: str
    event_id: str = field(default_factory=lambda: f"sysevt_{uuid4().hex[:10]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "message": self.message,
            "payload": self.payload,
        }

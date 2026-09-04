from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone


class ReceiptStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CACHED = "CACHED"
    INTERRUPTED = "INTERRUPTED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


@dataclass
class ArtifactRecord:
    artifact_id: str
    uri: str
    mime_type: str = "application/octet-stream"
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionReceipt:
    capability_id: str
    status: ReceiptStatus
    receipt_id: str = field(default_factory=lambda: f"rcpt_{uuid4().hex[:12]}")
    version: str = "1.0.0"
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[ArtifactRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cache_hit: bool = False
    error: Optional[Dict[str, Any]] = None
    diagnostics_session_id: Optional[str] = None
    run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

@dataclass
class RunContext:
    run_id: str = field(default_factory=lambda: f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"))
    version: str = "0.6.3"

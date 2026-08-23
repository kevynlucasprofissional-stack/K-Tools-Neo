
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json

@dataclass
class Event:
    timestamp: str
    run_id: str
    level: str
    component: str
    event: str
    message: str
    data: dict

    def to_dict(self):
        return asdict(self)

def create_event(ctx, level, component, event, message, data=None):
    return Event(
        timestamp=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        run_id=ctx.run_id,
        level=level,
        component=component,
        event=event,
        message=message,
        data=data or {},
    )

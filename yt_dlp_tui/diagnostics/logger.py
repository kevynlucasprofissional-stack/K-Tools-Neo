
from __future__ import annotations
import json, os, re
from .events import create_event
from .context import RunContext

_SECRET_KEYS = re.compile(r"(cookie|token|secret|password|authorization|credential)", re.I)

class DiagnosticLogger:
    def __init__(self, ctx=None, path="events.jsonl"):
        self.ctx = ctx or RunContext()
        self.path = path

    def sanitize(self, value):
        if isinstance(value, dict):
            return {k: ("<redacted>" if _SECRET_KEYS.search(str(k)) else self.sanitize(v)) for k,v in value.items()}
        if isinstance(value, list):
            return [self.sanitize(v) for v in value]
        return value

    def emit(self, component, event, message="", level="INFO", data=None):
        evt = create_event(self.ctx, level, component, event, message, self.sanitize(data or {}))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt.to_dict(), ensure_ascii=False)+"\n")
        return evt

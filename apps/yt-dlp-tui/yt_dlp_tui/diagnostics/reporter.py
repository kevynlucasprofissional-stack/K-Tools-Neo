from __future__ import annotations
import json
import os
import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path
from .anomalies import detect_anomalies


class DiagnosticReporter:
    def __init__(self, ctx, logger, base_dir=None):
        self.ctx = ctx
        self.logger = logger
        self.base_dir = Path(base_dir or os.getcwd()) / "YT-DLP-TUI-report"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _events(self):
        p = Path(self.logger.path)
        if not p.exists():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out

    def write(self, extra=None):
        events = self._events()
        payload = {
            "version": self.ctx.version,
            "run_id": self.ctx.run_id,
            "started_at": self.ctx.started_at,
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "duration_events": len(events),
            "system": {"python": platform.python_version(), "platform": platform.platform()},
            "events": events,
            "anomalies": detect_anomalies(events, (extra or {}).get("control"), (extra or {}).get("audit")),
            "extra": extra or {},
        }
        (self.base_dir / "events.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events), encoding="utf-8")
        (self.base_dir / "report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md = ["# YT-DLP TUI Report", "", f"Run ID: {self.ctx.run_id}", f"Version: {self.ctx.version}", "", "## Timeline"]
        for e in events:
            md.append(f"- {e.get('timestamp')} | {e.get('component')} | {e.get('event')} | {e.get('message')}")
        (self.base_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
        return self.base_dir

    def crash(self, exc):
        text = [
            "# YT-DLP TUI Crash Report",
            "",
            f"Run ID: {self.ctx.run_id}",
            "",
            "## Exception",
            "",
            traceback.format_exc(),
            "",
            "## Last events",
        ]
        for e in self._events()[-20:]:
            text.append(json.dumps(e, ensure_ascii=False))
        (self.base_dir / "CRASH_REPORT.md").write_text("\n".join(text), encoding="utf-8")

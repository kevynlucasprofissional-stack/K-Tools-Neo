from __future__ import annotations

import json
import logging
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .diagnostics import (
    DiagnosticKind,
    DiagnosticSeverity,
    DiagnosticsSession,
    redact_value,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class DiagnosticLogHandler(logging.Handler):
    """Bridge standard-library logging records into a DiagnosticsSession."""

    def __init__(self, session: DiagnosticsSession, *, component: str | None = None) -> None:
        super().__init__()
        self.session = session
        self.component = component

    @staticmethod
    def _severity(levelno: int) -> DiagnosticSeverity:
        if levelno >= logging.CRITICAL:
            return DiagnosticSeverity.CRITICAL
        if levelno >= logging.ERROR:
            return DiagnosticSeverity.ERROR
        if levelno >= logging.WARNING:
            return DiagnosticSeverity.WARNING
        if levelno >= logging.INFO:
            return DiagnosticSeverity.INFO
        return DiagnosticSeverity.DEBUG

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            context: dict[str, Any] = {
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "threadName": record.threadName,
                "processName": record.processName,
            }
            if record.exc_info:
                exc = record.exc_info[1]
                if exc is not None:
                    self.session.capture_exception(
                        exc,
                        message,
                        severity=self._severity(record.levelno),
                        category="python.logging",
                        component=self.component or record.name or "python.logging",
                        context=context,
                    )
                    return
            self.session.record(
                message,
                severity=self._severity(record.levelno),
                kind=DiagnosticKind.LOG,
                category="python.logging",
                component=self.component or record.name or "python.logging",
                context=context,
            )
        except Exception:
            self.handleError(record)


def recover_abandoned_sessions(
    root: str | Path,
    *,
    minimum_age_seconds: float = 3600.0,
) -> tuple[Path, ...]:
    """Create shareable reports for stale sessions that never finalized.

    The absence of ``report.json`` does not prove a process died. To avoid
    misclassifying a currently-running process, V1 only recovers sessions whose
    diagnostic stream has not been modified for at least ``minimum_age_seconds``.

    Callers may explicitly pass ``0`` only when they have independent evidence
    that no live process still owns the session (tests, controlled startup
    recovery after reboot, or a future ownership/lease mechanism).
    """
    if minimum_age_seconds < 0:
        raise ValueError("minimum_age_seconds must be >= 0")

    parent = Path(root).expanduser().resolve()
    if not parent.exists():
        return ()

    recovered: list[Path] = []
    now = time.time()
    for session_dir in sorted(path for path in parent.iterdir() if path.is_dir()):
        events_path = session_dir / "diagnostics.jsonl"
        report_path = session_dir / "report.json"
        if not events_path.exists() or report_path.exists():
            continue
        age_seconds = max(0.0, now - events_path.stat().st_mtime)
        if age_seconds < minimum_age_seconds:
            continue

        events: list[dict[str, Any]] = []
        parse_errors = 0
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    events.append(redact_value(parsed))
            except json.JSONDecodeError:
                parse_errors += 1

        first = events[0] if events else {}
        last = events[-1] if events else {}
        started_at = first.get("occurredAt")
        recovered_at = _utc_now()
        noteworthy = [
            event
            for event in events
            if event.get("severity") in {"WARNING", "ERROR", "CRITICAL"}
            or event.get("kind") in {"ANOMALY", "EXCEPTION"}
        ]
        report = {
            "schemaVersion": 1,
            "recoveredAbandonedSession": True,
            "session": {
                "sessionId": session_dir.name,
                "status": "ABANDONED_OR_INTERRUPTED",
                "startedAt": started_at,
                "recoveredAt": recovered_at,
                "lastRecordedAt": last.get("occurredAt"),
                "lastRunId": last.get("runId"),
                "lastWorkflowId": last.get("workflowId"),
                "lastNodeId": last.get("nodeId"),
                "staleAgeSeconds": age_seconds,
                "minimumAgeSeconds": minimum_age_seconds,
            },
            "summary": {
                "eventCount": len(events),
                "jsonlParseErrors": parse_errors,
                "noteworthyCount": len(noteworthy),
            },
            "lastEvent": last or None,
            "diagnosticHotspots": noteworthy[-20:],
            "events": events,
            "notice": (
                "The process did not generate a normal diagnostic finalization. "
                "The session was stale enough for explicit recovery, but this "
                "report does not infer the root cause."
            ),
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )
        markdown = [
            "# K-Tools Neo — Recovered Abandoned Diagnostic Session",
            "",
            f"- Session: `{session_dir.name}`",
            "- Status: **ABANDONED_OR_INTERRUPTED**",
            f"- First recorded event: {started_at or 'unknown'}",
            f"- Last recorded event: {last.get('occurredAt') or 'unknown'}",
            f"- Stale age at recovery: {age_seconds:.1f}s",
            f"- Events preserved: {len(events)}",
            f"- JSONL parse errors: {parse_errors}",
            "",
            "The previous process did not generate a normal final report. This can happen after a crash, forced termination or machine shutdown. Staleness is evidence of abandonment, not proof of a specific failure cause.",
            "",
            "## Last recorded event",
            "",
            f"```json\n{json.dumps(last or None, ensure_ascii=False, indent=2, sort_keys=True)}\n```",
            "",
        ]
        (session_dir / "report.md").write_text("\n".join(markdown), encoding="utf-8")

        bundle = session_dir / "support-bundle.zip"
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(session_dir.rglob("*")):
                if path.is_file() and path != bundle:
                    archive.write(path, path.relative_to(session_dir).as_posix())
        recovered.append(bundle)

    return tuple(recovered)

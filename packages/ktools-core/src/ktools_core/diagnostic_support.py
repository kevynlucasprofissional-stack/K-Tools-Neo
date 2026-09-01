from __future__ import annotations

import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .diagnostics import (
    DiagnosticKind,
    DiagnosticSeverity,
    DiagnosticsSession,
    redact_text,
    redact_value,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class DiagnosticLogHandler(logging.Handler):
    """Bridge standard-library logging records into a DiagnosticsSession.

    The handler records the operational log message and safe LogRecord metadata.
    It intentionally does not serialize arbitrary record.__dict__ values.
    """

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
            # Logging must never make the product fail. Follow logging.Handler's
            # conventional error path instead of re-raising into application code.
            self.handleError(record)


def recover_abandoned_sessions(root: str | Path) -> tuple[Path, ...]:
    """Create shareable reports for diagnostic sessions that never finalized.

    A directory is considered abandoned when it contains ``diagnostics.jsonl``
    but lacks ``report.json``. This covers process crashes, forced termination or
    machine shutdown where Python never had a chance to call ``finalize``.

    Recovery does not claim a root cause. It preserves the last durable diagnostic
    evidence and labels the session ``ABANDONED_OR_INTERRUPTED``.
    """
    parent = Path(root).expanduser().resolve()
    if not parent.exists():
        return ()

    recovered: list[Path] = []
    for session_dir in sorted(path for path in parent.iterdir() if path.is_dir()):
        events_path = session_dir / "diagnostics.jsonl"
        report_path = session_dir / "report.json"
        if not events_path.exists() or report_path.exists():
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
                "The process ended without a normal diagnostic finalization. "
                "This report preserves recorded evidence but does not infer the cause."
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
            f"- Events preserved: {len(events)}",
            f"- JSONL parse errors: {parse_errors}",
            "",
            "The previous process did not generate a normal final report. This can happen after a crash, forced termination or machine shutdown. The bundle contains the last durable evidence; it does not by itself establish the root cause.",
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

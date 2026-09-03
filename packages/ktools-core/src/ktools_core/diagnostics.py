from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
import traceback
import zipfile
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4

from .journal import RunEvent, to_json_safe


class DiagnosticSeverity(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DiagnosticKind(str, Enum):
    LOG = "LOG"
    DECISION = "DECISION"
    METRIC = "METRIC"
    BATCH = "BATCH"
    ANOMALY = "ANOMALY"
    EXCEPTION = "EXCEPTION"
    SUBPROCESS = "SUBPROCESS"
    LIFECYCLE = "LIFECYCLE"


_SECRET_KEY_RE = re.compile(
    r"(?:^|[_\-])(?:token|api[_\-]?key|password|passwd|secret|cookie|authorization|bearer|access[_\-]?key|refresh[_\-]?token|client[_\-]?secret)(?:$|[_\-])",
    re.IGNORECASE,
)
_SECRET_INLINE_RE = re.compile(
    r"(?i)(authorization\s*[:=]\s*bearer\s+|bearer\s+|api[_-]?key\s*[:=]\s*|token\s*[:=]\s*|password\s*[:=]\s*)([^\s,;]+)"
)
_URL_SECRET_RE = re.compile(
    r"(?i)([?&](?:token|api[_-]?key|access[_-]?token|key|secret)=)[^&#\s]+"
)
_MAX_CONTEXT_STRING = 4000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def redact_text(value: str, *, max_length: int | None = _MAX_CONTEXT_STRING) -> str:
    redacted = _SECRET_INLINE_RE.sub(lambda m: f"{m.group(1)}<redacted>", value)
    redacted = _URL_SECRET_RE.sub(lambda m: f"{m.group(1)}<redacted>", redacted)
    if max_length is not None and len(redacted) > max_length:
        return redacted[:max_length] + f"… <truncated {len(redacted) - max_length} chars>"
    return redacted


def redact_value(value: Any, *, key: str | None = None) -> Any:
    """Normalize diagnostic data for safe sharing."""
    if key is not None and _SECRET_KEY_RE.search(key):
        return "<redacted>"

    normalized = to_json_safe(value)
    if isinstance(normalized, str):
        return redact_text(normalized)
    if isinstance(normalized, Mapping):
        return {
            str(item_key): redact_value(item_value, key=str(item_key))
            for item_key, item_value in normalized.items()
        }
    if isinstance(normalized, list):
        return [redact_value(item) for item in normalized]
    return normalized


def redact_command(command: Sequence[str] | str) -> list[str] | str:
    if isinstance(command, str):
        return redact_text(command)
    redacted: list[str] = []
    secret_next = False
    for raw_part in command:
        part = str(raw_part)
        lower = part.lower()
        if secret_next:
            redacted.append("<redacted>")
            secret_next = False
            continue
        if lower in {
            "--token", "--api-key", "--api_key", "--password", "--secret",
            "--cookie", "--authorization", "--client-secret", "--client_secret",
        }:
            redacted.append(part)
            secret_next = True
            continue
        if any(lower.startswith(prefix) for prefix in (
            "--token=", "--api-key=", "--api_key=", "--password=", "--secret=",
            "--cookie=", "--authorization=", "--client-secret=", "--client_secret=",
        )):
            name = part.split("=", 1)[0]
            redacted.append(f"{name}=<redacted>")
            continue
        redacted.append(redact_text(part))
    return redacted


@dataclass(frozen=True)
class DiagnosticEvent:
    event_id: str
    occurred_at: str
    severity: DiagnosticSeverity
    kind: DiagnosticKind
    category: str
    component: str
    message: str
    run_id: str | None = None
    workflow_id: str | None = None
    node_id: str | None = None
    stage: str | None = None
    batch_id: str | None = None
    context: Mapping[str, Any] = field(default_factory=dict)
    exception: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "eventId": self.event_id,
            "occurredAt": self.occurred_at,
            "severity": self.severity.value,
            "kind": self.kind.value,
            "category": self.category,
            "component": self.component,
            "message": redact_text(self.message),
            "runId": self.run_id,
            "workflowId": self.workflow_id,
            "nodeId": self.node_id,
            "stage": self.stage,
            "batchId": self.batch_id,
            "context": redact_value(dict(self.context)),
            "exception": None if self.exception is None else redact_value(dict(self.exception)),
        }


@dataclass(frozen=True)
class SubprocessResult:
    process_id: str
    command: list[str] | str
    return_code: int | None
    duration_seconds: float
    stdout_path: str | None
    stderr_path: str | None
    timed_out: bool = False
    launch_error: str | None = None


_ACTIVE_SESSION: ContextVar[DiagnosticsSession | None] = ContextVar("diagnostics_session", default=None)


class DiagnosticsSession:
    """Run-scoped structured diagnostics with shareable end-of-run bundle."""

    def __init__(
        self,
        root: str | Path,
        *,
        session_id: str | None = None,
        component: str = "ktools-core",
        product_version: str | None = None,
    ) -> None:
        self.session_id = session_id or f"diag_{uuid4().hex}"
        self.component = component
        self.product_version = product_version
        self.root = Path(root).expanduser().resolve() / self.session_id
        self.raw_dir = self.root / "raw"
        self.root.mkdir(parents=True, exist_ok=False)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.root / "diagnostics.jsonl"
        self.session_path = self.root / "session.json"
        self.started_at = _utc_now()
        self._started_monotonic = time.monotonic()
        self._events: list[DiagnosticEvent] = []
        self._finalized = False
        self._terminal_status: str | None = None
        self._write_session_state(status="RUNNING")
        self.log(
            "Diagnostics session started",
            kind=DiagnosticKind.LIFECYCLE,
            category="diagnostics.session",
            context={"sessionId": self.session_id, "processId": os.getpid()},
        )

    @property
    def events(self) -> tuple[DiagnosticEvent, ...]:
        return tuple(self._events)

    def _write_session_state(
        self,
        *,
        status: str,
        run_id: str | None = None,
        workflow_id: str | None = None,
        ended_at: str | None = None,
    ) -> None:
        state = {
            "schemaVersion": 1,
            "sessionId": self.session_id,
            "status": status,
            "startedAt": self.started_at,
            "endedAt": ended_at,
            "runId": run_id,
            "workflowId": workflow_id,
            "processId": os.getpid(),
            "component": self.component,
            "productVersion": self.product_version,
        }
        self.session_path.write_text(
            json.dumps(redact_value(state), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )

    def record(
        self,
        message: str,
        *,
        severity: DiagnosticSeverity = DiagnosticSeverity.INFO,
        kind: DiagnosticKind = DiagnosticKind.LOG,
        category: str = "runtime",
        component: str | None = None,
        run_id: str | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None,
        stage: str | None = None,
        batch_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        exception: Mapping[str, Any] | None = None,
    ) -> DiagnosticEvent:
        if self._finalized:
            raise RuntimeError("DiagnosticsSession is already finalized")
        event = DiagnosticEvent(
            event_id=f"diag_event_{uuid4().hex}",
            occurred_at=_utc_now(),
            severity=severity,
            kind=kind,
            category=category,
            component=component or self.component,
            message=message,
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node_id,
            stage=stage,
            batch_id=batch_id,
            context=dict(context or {}),
            exception=None if exception is None else dict(exception),
        )
        self._events.append(event)
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            json.dump(event.to_dict(), handle, ensure_ascii=False, sort_keys=True, allow_nan=False)
            handle.write("\n")
        return event

    def log(self, message: str, **kwargs: Any) -> DiagnosticEvent:
        return self.record(message, **kwargs)

    def decision(self, message: str, *, reason: str, **kwargs: Any) -> DiagnosticEvent:
        context = dict(kwargs.pop("context", {}) or {})
        context["reason"] = reason
        return self.record(message, kind=DiagnosticKind.DECISION, context=context, **kwargs)

    def metric(self, name: str, value: Any, *, unit: str | None = None, **kwargs: Any) -> DiagnosticEvent:
        context = dict(kwargs.pop("context", {}) or {})
        context.update({"metric": name, "value": value})
        if unit is not None:
            context["unit"] = unit
        return self.record(f"Metric: {name}", kind=DiagnosticKind.METRIC, context=context, **kwargs)

    def batch(self, message: str, *, batch_id: str, **kwargs: Any) -> DiagnosticEvent:
        return self.record(message, kind=DiagnosticKind.BATCH, batch_id=batch_id, **kwargs)

    def anomaly(self, message: str, **kwargs: Any) -> DiagnosticEvent:
        severity = kwargs.pop("severity", DiagnosticSeverity.WARNING)
        return self.record(message, kind=DiagnosticKind.ANOMALY, severity=severity, **kwargs)

    def capture_exception(self, exc: BaseException, message: str | None = None, **kwargs: Any) -> DiagnosticEvent:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        exception = {
            "type": f"{type(exc).__module__}.{type(exc).__qualname__}",
            "message": str(exc),
            "traceback": tb,
        }
        return self.record(
            message or f"{type(exc).__name__}: {exc}",
            severity=kwargs.pop("severity", DiagnosticSeverity.ERROR),
            kind=DiagnosticKind.EXCEPTION,
            exception=exception,
            **kwargs,
        )

    def run_subprocess(
        self,
        command: Sequence[str] | str,
        *,
        cwd: str | Path | None = None,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
        shell: bool = False,
        check: bool = False,
        category: str = "subprocess",
        run_id: str | None = None,
        workflow_id: str | None = None,
        node_id: str | None = None,
    ) -> SubprocessResult:
        process_id = f"process_{uuid4().hex}"
        safe_command = redact_command(command)
        stdout_path = self.raw_dir / f"{process_id}.stdout.log"
        stderr_path = self.raw_dir / f"{process_id}.stderr.log"
        started = time.monotonic()
        self.record(
            "Subprocess started",
            kind=DiagnosticKind.SUBPROCESS,
            category=category,
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node_id,
            context={"processId": process_id, "command": safe_command, "cwd": None if cwd is None else str(cwd)},
        )
        try:
            completed = subprocess.run(
                command,
                cwd=None if cwd is None else str(cwd),
                env=None if env is None else dict(env),
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            duration = time.monotonic() - started
            stdout_path.write_text(redact_text(completed.stdout or "", max_length=None), encoding="utf-8")
            stderr_path.write_text(redact_text(completed.stderr or "", max_length=None), encoding="utf-8")
            severity = DiagnosticSeverity.INFO if completed.returncode == 0 else DiagnosticSeverity.ERROR
            self.record(
                "Subprocess completed" if completed.returncode == 0 else "Subprocess returned non-zero exit code",
                severity=severity,
                kind=DiagnosticKind.SUBPROCESS,
                category=category,
                run_id=run_id,
                workflow_id=workflow_id,
                node_id=node_id,
                context={
                    "processId": process_id,
                    "command": safe_command,
                    "returnCode": completed.returncode,
                    "durationSeconds": duration,
                    "stdoutFile": stdout_path.name,
                    "stderrFile": stderr_path.name,
                    "stdoutBytes": stdout_path.stat().st_size,
                    "stderrBytes": stderr_path.stat().st_size,
                },
            )
            result = SubprocessResult(
                process_id=process_id,
                command=safe_command,
                return_code=completed.returncode,
                duration_seconds=duration,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
            )
            if check and completed.returncode != 0:
                raise subprocess.CalledProcessError(completed.returncode, safe_command)
            return result
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            stdout_path.write_text(redact_text(stdout, max_length=None), encoding="utf-8")
            stderr_path.write_text(redact_text(stderr, max_length=None), encoding="utf-8")
            self.capture_exception(
                exc,
                "Subprocess timed out",
                category=category,
                run_id=run_id,
                workflow_id=workflow_id,
                node_id=node_id,
                context={"processId": process_id, "command": safe_command, "durationSeconds": duration},
            )
            return SubprocessResult(
                process_id=process_id,
                command=safe_command,
                return_code=None,
                duration_seconds=duration,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                timed_out=True,
                launch_error=str(exc),
            )
        except OSError as exc:
            duration = time.monotonic() - started
            self.capture_exception(
                exc,
                "Subprocess failed to launch",
                category=category,
                run_id=run_id,
                workflow_id=workflow_id,
                node_id=node_id,
                context={"processId": process_id, "command": safe_command, "durationSeconds": duration},
            )
            return SubprocessResult(
                process_id=process_id,
                command=safe_command,
                return_code=None,
                duration_seconds=duration,
                stdout_path=None,
                stderr_path=None,
                launch_error=str(exc),
            )

    def finalize(
        self,
        *,
        status: str,
        run_id: str | None = None,
        workflow_id: str | None = None,
        result_summary: Mapping[str, Any] | None = None,
        journal_events: Iterable[RunEvent] | None = None,
    ) -> Path:
        if self._finalized:
            return self.root / "support-bundle.zip"
        self._terminal_status = status
        self.record(
            "Diagnostics session finalized",
            kind=DiagnosticKind.LIFECYCLE,
            category="diagnostics.session",
            severity=DiagnosticSeverity.INFO if status.upper() == "SUCCEEDED" else DiagnosticSeverity.WARNING,
            run_id=run_id,
            workflow_id=workflow_id,
            context={"status": status},
        )
        ended_at = _utc_now()
        duration = time.monotonic() - self._started_monotonic
        event_dicts = [event.to_dict() for event in self._events]
        journal = [event.to_dict() for event in (journal_events or ())]
        report = self._build_report(
            status=status,
            ended_at=ended_at,
            duration_seconds=duration,
            run_id=run_id,
            workflow_id=workflow_id,
            result_summary=result_summary,
            events=event_dicts,
            journal_events=journal,
        )
        report_json = self.root / "report.json"
        report_md = self.root / "report.md"
        report_json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )
        report_md.write_text(self._render_markdown(report), encoding="utf-8")
        self._write_session_state(
            status=status,
            run_id=run_id,
            workflow_id=workflow_id,
            ended_at=ended_at,
        )
        bundle = self.root / "support-bundle.zip"
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.root.rglob("*")):
                if not path.is_file() or path == bundle:
                    continue
                archive.write(path, path.relative_to(self.root).as_posix())
        self._finalized = True
        return bundle

    def _build_report(
        self,
        *,
        status: str,
        ended_at: str,
        duration_seconds: float,
        run_id: str | None,
        workflow_id: str | None,
        result_summary: Mapping[str, Any] | None,
        events: list[dict[str, Any]],
        journal_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        severity_counts = {severity.value: 0 for severity in DiagnosticSeverity}
        kind_counts = {kind.value: 0 for kind in DiagnosticKind}
        for event in events:
            severity_counts[event["severity"]] = severity_counts.get(event["severity"], 0) + 1
            kind_counts[event["kind"]] = kind_counts.get(event["kind"], 0) + 1
        noteworthy = [
            event for event in events
            if event["severity"] in {"WARNING", "ERROR", "CRITICAL"}
            or event["kind"] in {"ANOMALY", "EXCEPTION"}
        ]
        hotspots = [
            {
                "component": event["component"],
                "category": event["category"],
                "message": event["message"],
                "severity": event["severity"],
                "nodeId": event.get("nodeId"),
                "stage": event.get("stage"),
                "batchId": event.get("batchId"),
            }
            for event in noteworthy[-20:]
        ]
        nodes = [event for event in events if event.get("nodeId") is not None]
        stages = [event for event in events if event.get("stage") is not None]
        raw_files = [
            path.relative_to(self.root).as_posix()
            for path in sorted(self.raw_dir.rglob("*"))
            if path.is_file()
        ]
        return {
            "schemaVersion": 1,
            "session": {
                "sessionId": self.session_id,
                "runId": run_id,
                "workflowId": workflow_id,
                "status": status,
                "startedAt": self.started_at,
                "endedAt": ended_at,
                "durationSeconds": duration_seconds,
            },
            "environment": {
                "productVersion": self.product_version,
                "python": sys.version.split()[0],
                "pythonImplementation": platform.python_implementation(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processId": os.getpid(),
                "currentWorkingDirectory": str(Path.cwd()),
            },
            "summary": {
                "eventCount": len(events),
                "severityCounts": severity_counts,
                "kindCounts": kind_counts,
                "noteworthyCount": len(noteworthy),
                "nodeEventCount": len(nodes),
                "stageEventCount": len(stages),
                "batchEventCount": sum(1 for event in events if event["kind"] == "BATCH"),
                "subprocessEventCount": sum(1 for event in events if event["kind"] == "SUBPROCESS"),
                "journalEventCount": len(journal_events),
            },
            "result": redact_value(dict(result_summary or {})),
            "nodeTimeline": nodes,
            "stages": stages,
            "decisions": [event for event in events if event["kind"] == "DECISION"],
            "batches": [event for event in events if event["kind"] == "BATCH"],
            "metrics": [event for event in events if event["kind"] == "METRIC"],
            "anomalies": [event for event in events if event["kind"] == "ANOMALY"],
            "errors": [event for event in events if event["severity"] in {"ERROR", "CRITICAL"}],
            "subprocesses": [event for event in events if event["kind"] == "SUBPROCESS"],
            "rawLogFiles": raw_files,
            "diagnosticHotspots": hotspots,
            "journalEvents": journal_events,
            "events": events,
        }

    @staticmethod
    def _render_markdown(report: Mapping[str, Any]) -> str:
        session = report["session"]
        summary = report["summary"]
        environment = report.get("environment") or {}
        lines = [
            "# K-Tools Neo — Diagnostic Report",
            "",
            f"- Session: `{session['sessionId']}`",
            f"- Run: `{session.get('runId') or 'n/a'}`",
            f"- Workflow: `{session.get('workflowId') or 'n/a'}`",
            f"- Status: **{session['status']}**",
            f"- Started: {session['startedAt']}",
            f"- Ended: {session['endedAt']}",
            f"- Duration: {session['durationSeconds']:.3f}s",
            "",
            "## Environment",
            "",
            f"- Product version: `{environment.get('productVersion') or 'unknown'}`",
            f"- Python: `{environment.get('python')}` ({environment.get('pythonImplementation')})",
            f"- Platform: `{environment.get('platform')}`",
            f"- Machine: `{environment.get('machine')}`",
            f"- Process ID: `{environment.get('processId')}`",
            f"- Working directory: `{environment.get('currentWorkingDirectory')}`",
            "",
            "## Summary",
            "",
            f"- Diagnostic events: {summary['eventCount']}",
            f"- Node-correlated events: {summary.get('nodeEventCount', 0)}",
            f"- Stage-correlated events: {summary.get('stageEventCount', 0)}",
            f"- Batch events: {summary.get('batchEventCount', 0)}",
            f"- Subprocess events: {summary.get('subprocessEventCount', 0)}",
            f"- Run Journal events: {summary.get('journalEventCount', 0)}",
            f"- Noteworthy warning/error/anomaly events: {summary['noteworthyCount']}",
            f"- Severity counts: `{json.dumps(summary['severityCounts'], sort_keys=True)}`",
            f"- Kind counts: `{json.dumps(summary['kindCounts'], sort_keys=True)}`",
            "",
        ]

        def add_event_section(title: str, events: Sequence[Mapping[str, Any]], empty: str) -> None:
            lines.extend([f"## {title}", ""])
            if not events:
                lines.append(empty)
                lines.append("")
                return
            for event in events:
                correlation = []
                if event.get("nodeId"):
                    correlation.append(f"node={event['nodeId']}")
                if event.get("stage"):
                    correlation.append(f"stage={event['stage']}")
                if event.get("batchId"):
                    correlation.append(f"batch={event['batchId']}")
                suffix = f" ({', '.join(correlation)})" if correlation else ""
                context = event.get("context") or {}
                context_text = f" — `{json.dumps(context, ensure_ascii=False, sort_keys=True)}`" if context else ""
                lines.append(
                    f"- {event.get('occurredAt')} — **{event.get('severity')}** {event.get('message')}{suffix}{context_text}"
                )
            lines.append("")

        hotspots = report.get("diagnosticHotspots") or []
        lines.extend(["## Diagnostic hotspots / possible failure points", ""])
        if not hotspots:
            lines.append("No warning/error/anomaly hotspots were recorded.")
        else:
            for item in hotspots:
                correlation = []
                for key, label in (("nodeId", "node"), ("stage", "stage"), ("batchId", "batch")):
                    if item.get(key):
                        correlation.append(f"{label}={item[key]}")
                suffix = f" ({', '.join(correlation)})" if correlation else ""
                lines.append(
                    f"- **{item['severity']}** `{item['component']}/{item['category']}`{suffix}: {item['message']}"
                )
        lines.extend([
            "",
            "> These are recorded warning/error/anomaly observations, not automatic root-cause conclusions.",
            "",
        ])

        add_event_section(
            "Executed nodes / steps",
            report.get("nodeTimeline") or [],
            "No node-correlated diagnostic events were recorded.",
        )
        add_event_section(
            "Stages",
            report.get("stages") or [],
            "No explicit stage events were recorded.",
        )
        add_event_section(
            "Batches / lots",
            report.get("batches") or [],
            "No explicit batch events were recorded.",
        )
        add_event_section(
            "System decisions",
            report.get("decisions") or [],
            "No explicit decision events were recorded.",
        )
        add_event_section(
            "Metrics / quality observations",
            report.get("metrics") or [],
            "No explicit metric events were recorded.",
        )
        add_event_section(
            "Anomalies / inconsistent results",
            report.get("anomalies") or [],
            "No anomaly events were recorded.",
        )
        add_event_section(
            "Subprocess / PowerShell / external runtime events",
            report.get("subprocesses") or [],
            "No subprocess events were recorded.",
        )

        lines.extend(["## Errors / failures", ""])
        errors = report.get("errors") or []
        if not errors:
            lines.append("No ERROR/CRITICAL diagnostic events were recorded.")
        else:
            for event in errors:
                node = f" node={event['nodeId']}" if event.get("nodeId") else ""
                lines.append(f"- **{event['severity']}**{node}: {event['message']}")
                if event.get("exception"):
                    lines.append(
                        f"  - Exception: `{event['exception'].get('type')}` — {event['exception'].get('message')}"
                    )
        lines.append("")

        lines.extend(["## Result / outputs", ""])
        result = report.get("result") or {}
        if result:
            lines.extend(["```json", json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
        else:
            lines.extend(["No explicit result summary was recorded.", ""])

        lines.extend(["## Run Journal lifecycle", ""])
        journal_events = report.get("journalEvents") or []
        if not journal_events:
            lines.append("No Run Journal events were attached to this report.")
        else:
            for event in journal_events:
                node = f" node={event.get('nodeId')}" if event.get("nodeId") else ""
                lines.append(f"- {event.get('occurredAt')} — `{event.get('eventType')}`{node}")
        lines.append("")

        lines.extend(["## Raw logs", ""])
        raw_files = report.get("rawLogFiles") or []
        if not raw_files:
            lines.append("No raw child-process logs were captured.")
        else:
            for raw_file in raw_files:
                lines.append(f"- `{raw_file}`")
        lines.extend([
            "",
            "## Files in this support bundle",
            "",
            "- `session.json`: session terminal/incomplete state metadata",
            "- `report.md`: human-readable execution reconstruction",
            "- `report.json`: complete machine-readable reconstruction",
            "- `diagnostics.jsonl`: ordered structured diagnostic stream",
            "- `raw/`: captured child-process stdout/stderr when present",
            "",
        ])
        return "\n".join(lines)

def record_subprocess(
    command: Sequence[str] | str,
    *,
    cwd: str | Path | None = None,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
    shell: bool = False,
    check: bool = False,
    category: str = "subprocess",
    run_id: str | None = None,
    workflow_id: str | None = None,
    node_id: str | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    session = _ACTIVE_SESSION.get()
    if session:
        result = session.run_subprocess(
            command,
            cwd=cwd,
            timeout=timeout,
            env=env,
            shell=shell,
            check=check,
            category=category,
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node_id,
        )
        stdout_text = None
        if result.stdout_path and Path(result.stdout_path).exists():
            stdout_text = Path(result.stdout_path).read_text(encoding="utf-8", errors="replace")
            
        stderr_text = None
        if result.stderr_path and Path(result.stderr_path).exists():
            stderr_text = Path(result.stderr_path).read_text(encoding="utf-8", errors="replace")
            
        if check and result.return_code != 0:
            raise subprocess.CalledProcessError(
                result.return_code,
                command,
                output=stdout_text,
                stderr=stderr_text,
            )
        return subprocess.CompletedProcess(
            args=command,
            returncode=result.return_code,
            stdout=stdout_text,
            stderr=stderr_text,
        )
    else:
        if kwargs.get("text") is None:
            kwargs["text"] = True
        return subprocess.run(command, cwd=cwd, timeout=timeout, env=env, shell=shell, check=check, **kwargs)

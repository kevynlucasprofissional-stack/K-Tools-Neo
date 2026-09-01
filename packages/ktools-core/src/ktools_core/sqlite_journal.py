from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .journal import (
    NodeRunStatus,
    RunEvent,
    RunEventType,
    RunStatus,
)


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    workflow_id: str
    status: RunStatus
    started_at: str
    ended_at: str | None = None
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class NodeRunRecord:
    run_id: str
    node_id: str
    node_type: str
    status: NodeRunStatus
    started_at: str
    ended_at: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    outputs: Any = None


@dataclass(frozen=True)
class RunDetail:
    run: RunRecord
    nodes: tuple[NodeRunRecord, ...]
    events: tuple[RunEvent, ...]


class SQLiteRunJournal:
    """Durable execution journal backed by Python's stdlib SQLite.

    Events are the append-only logical history. ``runs`` and ``node_runs`` are
    query-friendly projections updated in the same transaction as each event.
    """

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._initialize_schema()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteRunJournal":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    error_type TEXT,
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS node_runs (
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    outputs_json TEXT,
                    PRIMARY KEY (run_id, node_id),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    run_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    node_id TEXT,
                    node_type TEXT,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_runs_started_at
                    ON runs(started_at DESC);
                CREATE INDEX IF NOT EXISTS idx_events_run_sequence
                    ON events(run_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_node_runs_run
                    ON node_runs(run_id, node_id);
                """
            )

    @staticmethod
    def _json_dump(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    def record(self, event: RunEvent) -> None:
        payload = dict(event.payload or {})
        payload_json = self._json_dump(payload)

        with self._connection:
            if event.event_type is RunEventType.RUN_STARTED:
                self._connection.execute(
                    """
                    INSERT INTO runs(
                        run_id, workflow_id, status, started_at,
                        ended_at, error_type, error_message
                    ) VALUES (?, ?, ?, ?, NULL, NULL, NULL)
                    """,
                    (
                        event.run_id,
                        event.workflow_id,
                        RunStatus.RUNNING.value,
                        event.occurred_at,
                    ),
                )
            else:
                existing = self._connection.execute(
                    "SELECT 1 FROM runs WHERE run_id = ?", (event.run_id,)
                ).fetchone()
                if existing is None:
                    raise ValueError(
                        f"Run {event.run_id} must record RUN_STARTED before {event.event_type.value}"
                    )

            self._connection.execute(
                """
                INSERT INTO events(
                    event_id, run_id, workflow_id, node_id, node_type,
                    event_type, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.workflow_id,
                    event.node_id,
                    event.node_type,
                    event.event_type.value,
                    event.occurred_at,
                    payload_json,
                ),
            )

            self._apply_projection(event, payload)

    def _apply_projection(self, event: RunEvent, payload: dict[str, Any]) -> None:
        event_type = event.event_type

        if event_type is RunEventType.RUN_STARTED:
            return

        if event_type is RunEventType.NODE_STARTED:
            if event.node_id is None or event.node_type is None:
                raise ValueError("NODE_STARTED requires node_id and node_type")
            self._connection.execute(
                """
                INSERT INTO node_runs(
                    run_id, node_id, node_type, status, started_at,
                    ended_at, error_type, error_message, outputs_json
                ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """,
                (
                    event.run_id,
                    event.node_id,
                    event.node_type,
                    NodeRunStatus.RUNNING.value,
                    event.occurred_at,
                ),
            )
            return

        if event_type is RunEventType.NODE_SUCCEEDED:
            self._update_node_terminal(
                event,
                status=NodeRunStatus.SUCCEEDED,
                outputs=payload.get("outputs"),
            )
            return

        if event_type is RunEventType.NODE_FAILED:
            self._update_node_terminal(
                event,
                status=NodeRunStatus.FAILED,
                error_type=_optional_str(payload.get("errorType")),
                error_message=_optional_str(payload.get("errorMessage")),
            )
            return

        if event_type is RunEventType.NODE_INTERRUPTED:
            self._update_node_terminal(
                event,
                status=NodeRunStatus.INTERRUPTED,
                error_type="InterruptedExecution",
                error_message=_optional_str(payload.get("reason")),
            )
            return

        if event_type is RunEventType.RUN_SUCCEEDED:
            self._update_run_terminal(event, RunStatus.SUCCEEDED)
            return

        if event_type is RunEventType.RUN_FAILED:
            self._update_run_terminal(
                event,
                RunStatus.FAILED,
                error_type=_optional_str(payload.get("errorType")),
                error_message=_optional_str(payload.get("errorMessage")),
            )
            return

        if event_type is RunEventType.RUN_INTERRUPTED:
            self._update_run_terminal(
                event,
                RunStatus.INTERRUPTED,
                error_type="InterruptedExecution",
                error_message=_optional_str(payload.get("reason")),
            )
            return

        raise ValueError(f"Unsupported journal event type: {event_type.value}")

    def _update_node_terminal(
        self,
        event: RunEvent,
        *,
        status: NodeRunStatus,
        error_type: str | None = None,
        error_message: str | None = None,
        outputs: Any = None,
    ) -> None:
        if event.node_id is None:
            raise ValueError(f"{event.event_type.value} requires node_id")
        outputs_json = None if outputs is None else self._json_dump(outputs)
        cursor = self._connection.execute(
            """
            UPDATE node_runs
               SET status = ?, ended_at = ?, error_type = ?,
                   error_message = ?, outputs_json = ?
             WHERE run_id = ? AND node_id = ?
            """,
            (
                status.value,
                event.occurred_at,
                error_type,
                error_message,
                outputs_json,
                event.run_id,
                event.node_id,
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError(
                f"Node {event.run_id}/{event.node_id} must record NODE_STARTED before {event.event_type.value}"
            )

    def _update_run_terminal(
        self,
        event: RunEvent,
        status: RunStatus,
        *,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        cursor = self._connection.execute(
            """
            UPDATE runs
               SET status = ?, ended_at = ?, error_type = ?, error_message = ?
             WHERE run_id = ? AND status = ?
            """,
            (
                status.value,
                event.occurred_at,
                error_type,
                error_message,
                event.run_id,
                RunStatus.RUNNING.value,
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError(
                f"Run {event.run_id} is not RUNNING; cannot apply {event.event_type.value}"
            )

    def list_runs(self, limit: int = 100) -> tuple[RunRecord, ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        rows = self._connection.execute(
            """
            SELECT run_id, workflow_id, status, started_at, ended_at,
                   error_type, error_message
              FROM runs
             ORDER BY started_at DESC, run_id DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return tuple(_row_to_run(row) for row in rows)

    def get_run(self, run_id: str) -> RunRecord | None:
        row = self._connection.execute(
            """
            SELECT run_id, workflow_id, status, started_at, ended_at,
                   error_type, error_message
              FROM runs
             WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        return None if row is None else _row_to_run(row)

    def get_node_runs(self, run_id: str) -> tuple[NodeRunRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT run_id, node_id, node_type, status, started_at, ended_at,
                   error_type, error_message, outputs_json
              FROM node_runs
             WHERE run_id = ?
             ORDER BY started_at ASC, node_id ASC
            """,
            (run_id,),
        ).fetchall()
        return tuple(_row_to_node_run(row) for row in rows)

    def get_events(self, run_id: str) -> tuple[RunEvent, ...]:
        rows = self._connection.execute(
            """
            SELECT event_id, run_id, workflow_id, node_id, node_type,
                   event_type, occurred_at, payload_json
              FROM events
             WHERE run_id = ?
             ORDER BY sequence ASC
            """,
            (run_id,),
        ).fetchall()
        return tuple(_row_to_event(row) for row in rows)

    def get_run_detail(self, run_id: str) -> RunDetail | None:
        run = self.get_run(run_id)
        if run is None:
            return None
        return RunDetail(
            run=run,
            nodes=self.get_node_runs(run_id),
            events=self.get_events(run_id),
        )

    def reconcile_incomplete_runs(
        self,
        reason: str = "Previous process/session ended without a terminal event",
    ) -> tuple[str, ...]:
        """Explicitly mark persisted RUNNING runs/nodes as INTERRUPTED.

        Reconciliation is intentionally opt-in in V1. Automatically doing this
        in ``__init__`` could incorrectly mark a run owned by another live
        process as interrupted.
        """
        rows = self._connection.execute(
            """
            SELECT run_id, workflow_id
              FROM runs
             WHERE status = ?
             ORDER BY started_at ASC, run_id ASC
            """,
            (RunStatus.RUNNING.value,),
        ).fetchall()

        reconciled: list[str] = []
        for row in rows:
            run_id = str(row["run_id"])
            workflow_id = str(row["workflow_id"])
            node_rows = self._connection.execute(
                """
                SELECT node_id, node_type
                  FROM node_runs
                 WHERE run_id = ? AND status = ?
                 ORDER BY started_at ASC, node_id ASC
                """,
                (run_id, NodeRunStatus.RUNNING.value),
            ).fetchall()

            for node_row in node_rows:
                self.record(
                    RunEvent.create(
                        run_id=run_id,
                        workflow_id=workflow_id,
                        event_type=RunEventType.NODE_INTERRUPTED,
                        node_id=str(node_row["node_id"]),
                        node_type=str(node_row["node_type"]),
                        payload={"reason": reason},
                    )
                )

            self.record(
                RunEvent.create(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    event_type=RunEventType.RUN_INTERRUPTED,
                    payload={"reason": reason},
                )
            )
            reconciled.append(run_id)

        return tuple(reconciled)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _row_to_run(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        run_id=str(row["run_id"]),
        workflow_id=str(row["workflow_id"]),
        status=RunStatus(str(row["status"])),
        started_at=str(row["started_at"]),
        ended_at=None if row["ended_at"] is None else str(row["ended_at"]),
        error_type=None if row["error_type"] is None else str(row["error_type"]),
        error_message=None if row["error_message"] is None else str(row["error_message"]),
    )


def _row_to_node_run(row: sqlite3.Row) -> NodeRunRecord:
    outputs = None
    if row["outputs_json"] is not None:
        outputs = json.loads(str(row["outputs_json"]))
    return NodeRunRecord(
        run_id=str(row["run_id"]),
        node_id=str(row["node_id"]),
        node_type=str(row["node_type"]),
        status=NodeRunStatus(str(row["status"])),
        started_at=str(row["started_at"]),
        ended_at=None if row["ended_at"] is None else str(row["ended_at"]),
        error_type=None if row["error_type"] is None else str(row["error_type"]),
        error_message=None if row["error_message"] is None else str(row["error_message"]),
        outputs=outputs,
    )


def _row_to_event(row: sqlite3.Row) -> RunEvent:
    payload = json.loads(str(row["payload_json"]))
    return RunEvent(
        event_id=str(row["event_id"]),
        run_id=str(row["run_id"]),
        workflow_id=str(row["workflow_id"]),
        event_type=RunEventType(str(row["event_type"])),
        occurred_at=str(row["occurred_at"]),
        node_id=None if row["node_id"] is None else str(row["node_id"]),
        node_type=None if row["node_type"] is None else str(row["node_type"]),
        payload=payload,
    )

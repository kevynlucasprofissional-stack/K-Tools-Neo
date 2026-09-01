from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .cache_identity import ArtifactSnapshot, ArtifactSnapshotError, snapshot_artifact, validate_artifact_snapshot
from .journal import utc_now_iso
from .models import Artifact


class ArtifactRegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactRecord:
    observation_id: str
    artifact: Artifact
    run_id: str
    node_id: str
    output_port: str
    value_path: str
    source: str
    observed_at: str
    snapshot: ArtifactSnapshot | None
    snapshot_error: str | None = None


@dataclass(frozen=True)
class ArtifactRecordValidation:
    strongly_valid: bool | None
    reason: str
    current_sha256: str | None = None


def _walk_artifacts(value: Any, path: str = "$" ) -> list[tuple[str, Artifact]]:
    found: list[tuple[str, Artifact]] = []
    if isinstance(value, Artifact):
        found.append((path, value))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(_walk_artifacts(item, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found.extend(_walk_artifacts(item, f"{path}[{index}]"))
    return found


def validate_artifact_record(record: ArtifactRecord) -> ArtifactRecordValidation:
    if record.snapshot is None:
        return ArtifactRecordValidation(None, record.snapshot_error or "no-strong-snapshot")
    validation = validate_artifact_snapshot(record.snapshot)
    return ArtifactRecordValidation(
        validation.valid,
        validation.reason,
        current_sha256=validation.current_sha256,
    )


class ArtifactRegistry(Protocol):
    def observe_outputs(
        self,
        *,
        run_id: str,
        node_id: str,
        outputs: Mapping[str, Any],
        source: str,
    ) -> tuple[ArtifactRecord, ...]:
        ...


class SQLiteArtifactRegistry:
    """Persistent Artifact occurrences tied to run/node/output provenance.

    The registry owns metadata observations only; it never deletes or mutates the
    user's files. Strong file validity is stored when available, while unsupported
    Artifact kinds remain queryable with an explicit snapshot_error.
    """

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._initialize_schema()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteArtifactRegistry":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS artifact_observations (
                    observation_id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    produced_by TEXT,
                    mime_type TEXT,
                    metadata_json TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    output_port TEXT NOT NULL,
                    value_path TEXT NOT NULL,
                    source TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    snapshot_json TEXT,
                    snapshot_error TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_artifact_observations_artifact
                    ON artifact_observations(artifact_id, observed_at DESC);
                CREATE INDEX IF NOT EXISTS idx_artifact_observations_run
                    ON artifact_observations(run_id, node_id, output_port);
                """
            )

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    def observe_outputs(
        self,
        *,
        run_id: str,
        node_id: str,
        outputs: Mapping[str, Any],
        source: str,
    ) -> tuple[ArtifactRecord, ...]:
        source_label = str(source).upper()
        records: list[ArtifactRecord] = []
        for output_port, value in outputs.items():
            for value_path, artifact in _walk_artifacts(value):
                snapshot: ArtifactSnapshot | None = None
                snapshot_error: str | None = None
                try:
                    snapshot = snapshot_artifact(artifact)
                except (ArtifactSnapshotError, OSError) as exc:
                    snapshot_error = f"{type(exc).__name__}: {exc}"
                record = ArtifactRecord(
                    observation_id=f"artifact_observation_{uuid4().hex}",
                    artifact=artifact,
                    run_id=run_id,
                    node_id=node_id,
                    output_port=str(output_port),
                    value_path=value_path,
                    source=source_label,
                    observed_at=utc_now_iso(),
                    snapshot=snapshot,
                    snapshot_error=snapshot_error,
                )
                records.append(record)

        try:
            with self._connection:
                for record in records:
                    self._connection.execute(
                        """
                        INSERT INTO artifact_observations(
                            observation_id, artifact_id, artifact_type, uri,
                            produced_by, mime_type, metadata_json,
                            run_id, node_id, output_port, value_path, source,
                            observed_at, snapshot_json, snapshot_error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.observation_id,
                            record.artifact.id,
                            record.artifact.type.value,
                            record.artifact.uri,
                            record.artifact.produced_by,
                            record.artifact.mime_type,
                            self._dump(dict(record.artifact.metadata)),
                            record.run_id,
                            record.node_id,
                            record.output_port,
                            record.value_path,
                            record.source,
                            record.observed_at,
                            None if record.snapshot is None else self._dump(record.snapshot.to_dict()),
                            record.snapshot_error,
                        ),
                    )
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise ArtifactRegistryError(f"Artifact registry write failed: {exc}") from exc
        return tuple(records)

    def list_for_run(self, run_id: str) -> tuple[ArtifactRecord, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT * FROM artifact_observations
                 WHERE run_id = ?
                 ORDER BY observed_at ASC, observation_id ASC
                """,
                (run_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise ArtifactRegistryError(f"Artifact registry query failed: {exc}") from exc
        return tuple(_row_to_record(row) for row in rows)

    def list_for_artifact(self, artifact_id: str) -> tuple[ArtifactRecord, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT * FROM artifact_observations
                 WHERE artifact_id = ?
                 ORDER BY observed_at ASC, observation_id ASC
                """,
                (artifact_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise ArtifactRegistryError(f"Artifact registry query failed: {exc}") from exc
        return tuple(_row_to_record(row) for row in rows)


def _row_to_record(row: sqlite3.Row) -> ArtifactRecord:
    try:
        metadata = json.loads(str(row["metadata_json"]))
        raw_snapshot = None if row["snapshot_json"] is None else json.loads(str(row["snapshot_json"]))
        artifact = Artifact(
            id=str(row["artifact_id"]),
            type=__import__("ktools_core.models", fromlist=["DataType"]).DataType(str(row["artifact_type"])),
            uri=str(row["uri"]),
            produced_by=None if row["produced_by"] is None else str(row["produced_by"]),
            mime_type=None if row["mime_type"] is None else str(row["mime_type"]),
            metadata=metadata if isinstance(metadata, dict) else {},
        )
        snapshot = None if raw_snapshot is None else ArtifactSnapshot.from_dict(raw_snapshot)
    except Exception as exc:
        raise ArtifactRegistryError(f"Artifact registry row is corrupt: {exc}") from exc
    return ArtifactRecord(
        observation_id=str(row["observation_id"]),
        artifact=artifact,
        run_id=str(row["run_id"]),
        node_id=str(row["node_id"]),
        output_port=str(row["output_port"]),
        value_path=str(row["value_path"]),
        source=str(row["source"]),
        observed_at=str(row["observed_at"]),
        snapshot=snapshot,
        snapshot_error=None if row["snapshot_error"] is None else str(row["snapshot_error"]),
    )

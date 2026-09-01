from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from .cache_identity import (
    ArtifactSnapshot,
    ArtifactSnapshotError,
    snapshot_artifact,
    validate_artifact_snapshot,
)
from .models import Artifact


class CacheError(RuntimeError):
    pass


class CacheSerializationUnsupported(CacheError):
    pass


class CacheCorruptionError(CacheError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass(frozen=True)
class CacheEntry:
    signature: str
    node_type: str
    node_version: str
    origin_run_id: str
    origin_node_id: str
    outputs: dict[str, Any]
    artifact_snapshots: tuple[ArtifactSnapshot, ...]
    created_at: str
    last_used_at: str | None = None


@dataclass(frozen=True)
class CacheEntryValidation:
    valid: bool
    reason: str
    artifact_uri: str | None = None
    artifact_reason: str | None = None


_ENVELOPE = "__ktoolsCacheEnvelope__"


def _encode_value(value: Any, snapshots: list[ArtifactSnapshot]) -> Any:
    """Encode cache output without marker collisions with user JSON.

    Every container is wrapped in an internal envelope. A user mapping containing
    keys that resemble K-Tools internals is itself encoded as a mapping envelope,
    so it can never be mistaken for an Artifact marker during decode.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CacheSerializationUnsupported("Non-finite float cannot be cached")
        return value
    if isinstance(value, Artifact):
        try:
            snapshot = snapshot_artifact(value)
        except (ArtifactSnapshotError, OSError) as exc:
            raise CacheSerializationUnsupported(
                f"Artifact output is not strongly cache-valid: {exc}"
            ) from exc
        snapshots.append(snapshot)
        return {
            _ENVELOPE: "artifact",
            "value": _encode_value(value.to_dict(), snapshots),
        }
    if isinstance(value, Path):
        raise CacheSerializationUnsupported(
            "Path outputs are not cache-safe; use a file Artifact with strong validity"
        )
    if isinstance(value, Mapping):
        items: list[list[Any]] = []
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            if not isinstance(key, str):
                raise CacheSerializationUnsupported(
                    f"Cache output mappings require string keys, got {type(key).__name__}"
                )
            items.append([key, _encode_value(item, snapshots)])
        return {_ENVELOPE: "mapping", "items": items}
    if isinstance(value, list):
        return {_ENVELOPE: "list", "items": [_encode_value(item, snapshots) for item in value]}
    if isinstance(value, tuple):
        return {_ENVELOPE: "tuple", "items": [_encode_value(item, snapshots) for item in value]}
    raise CacheSerializationUnsupported(
        f"Unsupported cache output type: {type(value).__module__}.{type(value).__qualname__}"
    )


def _decode_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if not isinstance(value, dict):
        raise CacheCorruptionError(f"Unsupported encoded cache value: {type(value).__name__}")

    kind = value.get(_ENVELOPE)
    if kind == "artifact":
        if set(value) != {_ENVELOPE, "value"}:
            raise CacheCorruptionError("Cached Artifact envelope has unexpected fields")
        raw = _decode_value(value["value"])
        if not isinstance(raw, dict):
            raise CacheCorruptionError("Cached Artifact payload is not an object")
        try:
            return Artifact.from_dict(raw)
        except Exception as exc:
            raise CacheCorruptionError(f"Cached Artifact payload is invalid: {exc}") from exc

    if kind == "mapping":
        if set(value) != {_ENVELOPE, "items"} or not isinstance(value["items"], list):
            raise CacheCorruptionError("Cached mapping envelope is invalid")
        decoded: dict[str, Any] = {}
        for pair in value["items"]:
            if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str):
                raise CacheCorruptionError("Cached mapping item is invalid")
            if pair[0] in decoded:
                raise CacheCorruptionError(f"Duplicate cached mapping key: {pair[0]}")
            decoded[pair[0]] = _decode_value(pair[1])
        return decoded

    if kind in {"list", "tuple"}:
        if set(value) != {_ENVELOPE, "items"} or not isinstance(value["items"], list):
            raise CacheCorruptionError(f"Cached {kind} envelope is invalid")
        decoded_items = [_decode_value(item) for item in value["items"]]
        return decoded_items if kind == "list" else tuple(decoded_items)

    raise CacheCorruptionError("Unknown or missing cache envelope type")


def encode_cached_outputs(outputs: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[ArtifactSnapshot, ...]]:
    snapshots: list[ArtifactSnapshot] = []
    encoded = _encode_value(dict(outputs), snapshots)
    if not isinstance(encoded, dict):
        raise CacheSerializationUnsupported("Node outputs must encode to an object")
    return encoded, tuple(snapshots)


def decode_cached_outputs(encoded: Mapping[str, Any]) -> dict[str, Any]:
    decoded = _decode_value(dict(encoded))
    if not isinstance(decoded, dict):
        raise CacheCorruptionError("Cached node outputs did not decode to an object")
    return decoded


def validate_cache_entry(entry: CacheEntry) -> CacheEntryValidation:
    for snapshot in entry.artifact_snapshots:
        try:
            result = validate_artifact_snapshot(snapshot)
        except (ArtifactSnapshotError, OSError) as exc:
            return CacheEntryValidation(
                False,
                "artifact-validation-error",
                artifact_uri=snapshot.uri,
                artifact_reason=type(exc).__name__,
            )
        if not result.valid:
            return CacheEntryValidation(
                False,
                "artifact-invalid",
                artifact_uri=snapshot.uri,
                artifact_reason=result.reason,
            )
    return CacheEntryValidation(True, "valid")


class NodeCache(Protocol):
    def get(self, signature: str) -> CacheEntry | None:
        ...

    def put(
        self,
        *,
        signature: str,
        node_type: str,
        node_version: str,
        origin_run_id: str,
        origin_node_id: str,
        outputs: Mapping[str, Any],
    ) -> CacheEntry:
        ...

    def mark_used(self, signature: str) -> None:
        ...

    def invalidate(self, signature: str) -> None:
        ...


class SQLiteNodeCache:
    """Conservative local semantic cache backed by stdlib SQLite."""

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

    def __enter__(self) -> "SQLiteNodeCache":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS node_cache (
                    signature TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    node_version TEXT NOT NULL,
                    origin_run_id TEXT NOT NULL,
                    origin_node_id TEXT NOT NULL,
                    outputs_json TEXT NOT NULL,
                    artifact_snapshots_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_node_cache_type_version
                    ON node_cache(node_type, node_version);
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

    def get(self, signature: str) -> CacheEntry | None:
        try:
            row = self._connection.execute(
                """
                SELECT signature, node_type, node_version, origin_run_id,
                       origin_node_id, outputs_json, artifact_snapshots_json,
                       created_at, last_used_at
                  FROM node_cache
                 WHERE signature = ?
                """,
                (signature,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise CacheError(f"SQLite cache read failed: {exc}") from exc
        if row is None:
            return None
        try:
            encoded_outputs = json.loads(str(row["outputs_json"]))
            raw_snapshots = json.loads(str(row["artifact_snapshots_json"]))
            if not isinstance(encoded_outputs, dict) or not isinstance(raw_snapshots, list):
                raise CacheCorruptionError("Cache row has invalid JSON shapes")
            outputs = decode_cached_outputs(encoded_outputs)
            snapshots = tuple(ArtifactSnapshot.from_dict(item) for item in raw_snapshots)
        except CacheError:
            raise
        except Exception as exc:
            raise CacheCorruptionError(f"Could not decode cache row: {exc}") from exc

        return CacheEntry(
            signature=str(row["signature"]),
            node_type=str(row["node_type"]),
            node_version=str(row["node_version"]),
            origin_run_id=str(row["origin_run_id"]),
            origin_node_id=str(row["origin_node_id"]),
            outputs=outputs,
            artifact_snapshots=snapshots,
            created_at=str(row["created_at"]),
            last_used_at=None if row["last_used_at"] is None else str(row["last_used_at"]),
        )

    def put(
        self,
        *,
        signature: str,
        node_type: str,
        node_version: str,
        origin_run_id: str,
        origin_node_id: str,
        outputs: Mapping[str, Any],
    ) -> CacheEntry:
        encoded_outputs, snapshots = encode_cached_outputs(outputs)
        created_at = _utc_now()
        snapshots_payload = [snapshot.to_dict() for snapshot in snapshots]
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO node_cache(
                        signature, node_type, node_version, origin_run_id,
                        origin_node_id, outputs_json, artifact_snapshots_json,
                        created_at, last_used_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    ON CONFLICT(signature) DO UPDATE SET
                        node_type = excluded.node_type,
                        node_version = excluded.node_version,
                        origin_run_id = excluded.origin_run_id,
                        origin_node_id = excluded.origin_node_id,
                        outputs_json = excluded.outputs_json,
                        artifact_snapshots_json = excluded.artifact_snapshots_json,
                        created_at = excluded.created_at,
                        last_used_at = NULL
                    """,
                    (
                        signature,
                        node_type,
                        node_version,
                        origin_run_id,
                        origin_node_id,
                        self._dump(encoded_outputs),
                        self._dump(snapshots_payload),
                        created_at,
                    ),
                )
        except sqlite3.Error as exc:
            raise CacheError(f"SQLite cache write failed: {exc}") from exc
        entry = self.get(signature)
        if entry is None:
            raise CacheError("Cache entry disappeared immediately after write")
        return entry

    def mark_used(self, signature: str) -> None:
        try:
            with self._connection:
                self._connection.execute(
                    "UPDATE node_cache SET last_used_at = ? WHERE signature = ?",
                    (_utc_now(), signature),
                )
        except sqlite3.Error as exc:
            raise CacheError(f"SQLite cache touch failed: {exc}") from exc

    def invalidate(self, signature: str) -> None:
        try:
            with self._connection:
                self._connection.execute("DELETE FROM node_cache WHERE signature = ?", (signature,))
        except sqlite3.Error as exc:
            raise CacheError(f"SQLite cache invalidation failed: {exc}") from exc

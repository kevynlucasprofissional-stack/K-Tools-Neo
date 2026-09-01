from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from .models import Artifact, CachePolicy, DataType, NodeDefinition


class ArtifactSnapshotError(ValueError):
    pass


class UnsupportedArtifactError(ArtifactSnapshotError):
    pass


class ArtifactChangedDuringObservation(ArtifactSnapshotError):
    pass


class CacheSignatureUnsupported(TypeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _path_from_file_uri(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme.lower() != "file":
        raise UnsupportedArtifactError(f"Strong V1 validity supports only file:// URIs, got: {parsed.scheme or 'no scheme'}")
    if parsed.netloc not in {"", "localhost"}:
        raise UnsupportedArtifactError("Network/UNC file URI validity is not supported in V1")
    raw_path = url2pathname(unquote(parsed.path))
    if os.name == "nt" and len(raw_path) >= 3 and raw_path[0] in {"/", "\\"} and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return Path(raw_path).resolve()


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactSnapshot:
    artifact_type: DataType
    uri: str
    local_path: str
    size_bytes: int
    mtime_ns: int
    sha256: str
    observed_at: str

    @property
    def content_identity(self) -> dict[str, Any]:
        """Stable semantic identity, intentionally excluding random Artifact id/run."""
        return {
            "type": self.artifact_type.value,
            "sizeBytes": self.size_bytes,
            "sha256": self.sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifactType": self.artifact_type.value,
            "uri": self.uri,
            "localPath": self.local_path,
            "sizeBytes": self.size_bytes,
            "mtimeNs": self.mtime_ns,
            "sha256": self.sha256,
            "observedAt": self.observed_at,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ArtifactSnapshot":
        return cls(
            artifact_type=DataType(str(raw["artifactType"])),
            uri=str(raw["uri"]),
            local_path=str(raw["localPath"]),
            size_bytes=int(raw["sizeBytes"]),
            mtime_ns=int(raw["mtimeNs"]),
            sha256=str(raw["sha256"]),
            observed_at=str(raw["observedAt"]),
        )


@dataclass(frozen=True)
class ArtifactValidationResult:
    valid: bool
    reason: str
    current_size_bytes: int | None = None
    current_mtime_ns: int | None = None
    current_sha256: str | None = None


def snapshot_artifact(artifact: Artifact) -> ArtifactSnapshot:
    if artifact.type is DataType.FOLDER:
        raise UnsupportedArtifactError("Directory Artifact strong validity is not supported in V1")
    path = _path_from_file_uri(artifact.uri)
    if not path.exists():
        raise ArtifactSnapshotError(f"Artifact file does not exist: {path}")
    if not path.is_file():
        raise ArtifactSnapshotError(f"Artifact URI does not resolve to a file: {path}")

    before = path.stat()
    digest = _sha256_file(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ArtifactChangedDuringObservation(
            f"Artifact changed while being hashed: {path}"
        )

    return ArtifactSnapshot(
        artifact_type=artifact.type,
        uri=path.as_uri(),
        local_path=str(path),
        size_bytes=after.st_size,
        mtime_ns=after.st_mtime_ns,
        sha256=digest,
        observed_at=_utc_now(),
    )


def validate_artifact_snapshot(snapshot: ArtifactSnapshot) -> ArtifactValidationResult:
    path = Path(snapshot.local_path)
    if not path.exists():
        return ArtifactValidationResult(False, "missing")
    if not path.is_file():
        return ArtifactValidationResult(False, "not-a-file")

    before = path.stat()
    if before.st_size != snapshot.size_bytes:
        return ArtifactValidationResult(
            False,
            "size-changed",
            current_size_bytes=before.st_size,
            current_mtime_ns=before.st_mtime_ns,
        )
    if before.st_mtime_ns != snapshot.mtime_ns:
        return ArtifactValidationResult(
            False,
            "mtime-changed",
            current_size_bytes=before.st_size,
            current_mtime_ns=before.st_mtime_ns,
        )

    digest = _sha256_file(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        return ArtifactValidationResult(
            False,
            "changed-during-validation",
            current_size_bytes=after.st_size,
            current_mtime_ns=after.st_mtime_ns,
            current_sha256=digest,
        )
    if digest != snapshot.sha256:
        return ArtifactValidationResult(
            False,
            "content-changed",
            current_size_bytes=after.st_size,
            current_mtime_ns=after.st_mtime_ns,
            current_sha256=digest,
        )
    return ArtifactValidationResult(
        True,
        "valid",
        current_size_bytes=after.st_size,
        current_mtime_ns=after.st_mtime_ns,
        current_sha256=digest,
    )


def _semantic_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CacheSignatureUnsupported("Non-finite float cannot participate in a cache signature")
        return value
    if isinstance(value, Enum):
        return _semantic_value(value.value)
    if isinstance(value, ArtifactSnapshot):
        return {"__artifactSnapshot__": value.content_identity}
    if isinstance(value, Artifact):
        snapshot = snapshot_artifact(value)
        return {"__artifact__": snapshot.content_identity}
    if isinstance(value, Path):
        # Raw paths are semantic values but are not implicitly content-hashed.
        # Capability owners that mean 'file content' should use Artifact inputs.
        return {"__path__": str(value.expanduser().resolve())}
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, (str, int, float, bool)):
                raise CacheSignatureUnsupported(
                    f"Unsupported mapping key type in cache signature: {type(key).__name__}"
                )
            result[str(key)] = _semantic_value(item)
        return {key: result[key] for key in sorted(result)}
    if isinstance(value, (list, tuple)):
        return [_semantic_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_semantic_value(item) for item in value]
        try:
            return sorted(
                converted,
                key=lambda item: json.dumps(
                    item, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
                ),
            )
        except TypeError as exc:
            raise CacheSignatureUnsupported("Set contains non-canonical cache values") from exc
    raise CacheSignatureUnsupported(
        f"Unsupported cache-signature value type: {type(value).__module__}.{type(value).__qualname__}"
    )


def canonical_cache_payload(
    definition: NodeDefinition,
    *,
    config: Mapping[str, Any],
    inputs: Mapping[str, Any],
    signature_extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if definition.cache_policy is not CachePolicy.PURE:
        raise CacheSignatureUnsupported(
            f"Node {definition.type_id} is not cacheable (policy={definition.cache_policy.value})"
        )
    return {
        "schemaVersion": 1,
        "nodeType": definition.type_id,
        "nodeVersion": definition.version,
        "config": _semantic_value(dict(config)),
        "inputs": _semantic_value(dict(inputs)),
        "extras": _semantic_value(dict(signature_extras or {})),
    }


def build_cache_signature(
    definition: NodeDefinition,
    *,
    config: Mapping[str, Any],
    inputs: Mapping[str, Any],
    signature_extras: Mapping[str, Any] | None = None,
) -> str:
    payload = canonical_cache_payload(
        definition,
        config=config,
        inputs=inputs,
        signature_extras=signature_extras,
    )
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

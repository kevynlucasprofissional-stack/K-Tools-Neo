"""Shared file-producing orchestration between the direct API and the node.

The actual split semantics live in :mod:`ktools_json.capability` (the single
implementation owner). This module turns a split plan into real part files it,
and is intentionally the *only* place that writes output files, so the direct
API and the workflow node share every byte of file behavior.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .capability import (
    JsonSplitError,
    SplitOptions,
    replace_at_path,
    split_json_document,
)

DEFAULT_PREFIX = "json_parte"


class OutputCollisionError(JsonSplitError):
    """A target part file already exists and ``overwrite`` is disabled."""


@dataclass(frozen=True)
class JsonPart:
    """Deterministic artifact-shaped record for one written part."""

    index: int
    name: str
    uri: str
    size_bytes: int
    item_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "uri": self.uri,
            "sizeBytes": self.size_bytes,
            "itemCount": self.item_count,
            "kind": "file",
            "type": "json",
        }


@dataclass(frozen=True)
class SplitResult:
    """Outcome of one split-and-write operation."""

    output_dir: str
    parts: tuple[JsonPart, ...]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outputDir": self.output_dir,
            "parts": [part.to_dict() for part in self.parts],
            "summary": dict(self.summary),
        }


def safe_prefix(stem: str) -> str:
    """Normalize an output prefix into a filesystem-safe token."""
    if not isinstance(stem, str):
        raise JsonSplitError(f"prefix must be a string, got {stem!r}")
    cleaned = re.sub(r"[^A-Za-z0-9_.\-À-ÿ]+", "_", stem.strip()).strip("._")
    return cleaned or DEFAULT_PREFIX


def part_path(output_dir: Path, prefix: str, index: int, count: int) -> Path:
    """Deterministic part file name: ``{prefix}_parte_{i}_de_{count}.json``."""
    width = max(2, len(str(count)))
    return output_dir / f"{prefix}_parte_{index:0{width}d}_de_{count:0{width}d}.json"


def write_json_atomic(path: Path, data: Any) -> None:
    """Write JSON to ``path`` via a temp file + ``os.replace`` (atomic per file)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.stem}_", suffix=".tmp", dir=str(path.parent)
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _validate_written(path: Path) -> None:
    """Post-write validation: the generated file must parse back as JSON."""
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise JsonSplitError(f"Written part failed JSON validation: {path}") from exc


def file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def split_and_write(
    data: Any,
    options: SplitOptions,
    output_dir: str | Path,
    *,
    prefix: str = DEFAULT_PREFIX,
    overwrite: bool = False,
) -> SplitResult:
    """Split ``data`` and write each part as a standalone JSON file.

    Contract:

    - the plan comes from ``capability.split_json_document`` (single owner);
    - ``output_dir`` is created if absent and must be a directory;
    - destinations are validated *before* any write: if a target part file
      already exists and ``overwrite`` is false, an all-or-nothing
      ``OutputCollisionError`` is raised and nothing is written;
    - each part is written atomically (temp + ``os.replace``) and then
      re-read/parsed; a mid-write failure may leave already-emitted earlier
      parts on disk but never leaves a single part file incomplete.
    """
    plan = split_json_document(data, options)

    if not isinstance(output_dir, (str, Path)):
        raise JsonSplitError(f"output_dir must be a path, got {type(output_dir).__name__}")
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if not dest.is_dir():
        raise JsonSplitError(f"output_dir is not a directory: {dest}")

    safe = safe_prefix(prefix)
    if not isinstance(overwrite, bool):
        raise JsonSplitError(f"overwrite must be a boolean, got {overwrite!r}")

    paths = [
        part_path(dest, safe, index, plan.part_count)
        for index in range(1, plan.part_count + 1)
    ]

    if not overwrite:
        collisions = [path for path in paths if path.exists()]
        if collisions:
            raise OutputCollisionError(
                "Refusing to overwrite existing output file(s): "
                + ", ".join(str(path) for path in collisions)
                + ". Set overwrite=True to replace them."
            )

    parts: list[JsonPart] = []
    for index, chunk in enumerate(plan.chunks, start=1):
        path = paths[index - 1]
        part_data = replace_at_path(data, plan.list_path, chunk)
        write_json_atomic(path, part_data)
        _validate_written(path)
        parts.append(
            JsonPart(
                index=index,
                name=path.name,
                uri=file_uri(path),
                size_bytes=path.stat().st_size,
                item_count=len(chunk),
            )
        )

    summary = {
        "rootType": plan.root_type,
        "listPath": plan.list_path_label,
        "itemCount": plan.item_count,
        "partCount": plan.part_count,
        "outputSizes": [part.size_bytes for part in parts],
        "estimatedSizes": list(plan.estimated_sizes),
    }
    return SplitResult(output_dir=str(dest), parts=tuple(parts), summary=summary)
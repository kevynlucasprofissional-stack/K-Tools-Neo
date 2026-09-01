"""Public direct API for the JSON split capability (one implementation owner).

Thin layer: resolve and validate the source document, then delegate the split
and write to ``writer.split_and_write`` -- the same orchestration used by the
``json.split`` workflow node. No splitting logic lives here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .capability import JsonSplitError, make_options
from .writer import SplitResult, split_and_write

_READ_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1")


class JsonSourceError(JsonSplitError):
    """Source file is missing, is not a file, or cannot be read as text."""


class InvalidJsonDocumentError(JsonSplitError):
    """Source exists but its content is not valid JSON."""


def read_json_document(source: str | Path) -> Any:
    """Read and parse a JSON source file, classifying the common failure modes.

    Mirrors the legacy GUI's encoding fallback behavior (``utf-8``,
    ``utf-8-sig``, ``latin-1``). Distinguishes a missing/unreadable file from
    an invalid-JSON document.
    """
    path = Path(source)
    if not path.exists():
        raise JsonSourceError(f"JSON source file does not exist: {path}")
    if not path.is_file():
        raise JsonSourceError(f"JSON source is not a file: {path}")

    decode_errors: list[str] = []
    json_errors: list[tuple[str, json.JSONDecodeError]] = []

    for encoding in _READ_ENCODINGS:
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
            continue
        except OSError as exc:
            raise JsonSourceError(f"Could not open JSON source file: {exc}") from exc

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            json_errors.append((encoding, exc))
            continue

    if json_errors:
        encoding, exc = json_errors[0]
        raise InvalidJsonDocumentError(
            f"Invalid JSON in {path}: using {encoding}, line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    detail = "; ".join(decode_errors[:3]) if decode_errors else "encoding not recognized"
    raise JsonSourceError(f"Could not read source as JSON. Details: {detail}")


def split_json(
    source: str | Path,
    output_dir: str | Path,
    *,
    mode: str | None = None,
    parts: int | None = None,
    target_bytes: int | None = None,
    prefix: str = "json_parte",
    overwrite: bool = False,
) -> SplitResult:
    """Split the JSON document at ``source`` and write parts under ``output_dir``.

    Returns a deterministic :class:`SplitResult` with artifact-shaped part
    records and a summary. Raises classified :class:`JsonSplitError` subtypes
    on invalid configuration, missing/invalid source, no splittable list, or
    output collisions.
    """
    data = read_json_document(source)
    options = make_options(mode=mode, parts=parts, target_bytes=target_bytes)
    return split_and_write(
        data, options, output_dir, prefix=prefix, overwrite=overwrite
    )
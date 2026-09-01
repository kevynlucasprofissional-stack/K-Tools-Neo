"""Pure JSON-splitting capability -- the single implementation owner (OC-001).

This module owns *all* transformation semantics for splitting a JSON document
into parts. It performs no I/O and is deterministic given the same input and
options. Both the direct API (:mod:`ktools_json.api`) and the workflow node
(:mod:`ktools_json.node`) reach this code through the shared file-producing
orchestration in :mod:`ktools_json.writer`.

Behavior source: the split JSON tools of the legacy GUI
``K Tools Neo - Versao Estavel 2.py`` (``split_json_file`` and helpers). This
module is the extraction/elevation of that existing product behavior into the
new platform.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Sequence, Union

JsonPath = tuple[Union[str, int], ...]


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------


class JsonSplitError(ValueError):
    """Base error for the JSON split capability."""


class InvalidModeError(JsonSplitError):
    """``mode`` is not ``parts`` or ``size``."""


class InvalidPartsError(JsonSplitError):
    """``parts`` is not a positive integer."""


class InvalidTargetSizeError(JsonSplitError):
    """``target_bytes`` is not a positive integer."""


class NoMainListError(JsonSplitError):
    """The document has no splittable main list with items."""


class EmptyMainListError(JsonSplitError):
    """The detected main list is empty; nothing to split."""


# ---------------------------------------------------------------------------
# Split options
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SplitOptions:
    """Validated split configuration.

    ``parts`` is required when ``mode == "parts"``; ``target_bytes`` is required
    when ``mode == "size"``. Validation happens at construction so an invalid
    configuration fails with a classified error before any work is attempted.
    """

    mode: str = "parts"
    parts: int | None = None
    target_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("parts", "size"):
            raise InvalidModeError(f"mode must be 'parts' or 'size', got {self.mode!r}")
        if self.mode == "parts":
            if self.parts is None:
                raise InvalidPartsError("parts is required when mode='parts'")
            if isinstance(self.parts, bool) or not isinstance(self.parts, int) or self.parts < 1:
                raise InvalidPartsError(f"parts must be a positive integer, got {self.parts!r}")
        else:
            if self.target_bytes is None:
                raise InvalidTargetSizeError("target_bytes is required when mode='size'")
            if (
                isinstance(self.target_bytes, bool)
                or not isinstance(self.target_bytes, int)
                or self.target_bytes <= 0
            ):
                raise InvalidTargetSizeError(
                    f"target_bytes must be a positive integer, got {self.target_bytes!r}"
                )


def make_options(
    mode: str | None = None,
    parts: int | None = None,
    target_bytes: int | None = None,
) -> SplitOptions:
    """Build validated options with the legacy default of ``parts=2``."""
    if parts is None and (mode or "parts") == "parts":
        parts = 2
    return SplitOptions(mode=mode or "parts", parts=parts, target_bytes=target_bytes)


# ---------------------------------------------------------------------------
# Structural helpers (faithful to legacy behavior)
# ---------------------------------------------------------------------------


def json_path_label(path: JsonPath) -> str:
    """Render a semantic JSON path label (``$``, ``$.records``, ``$['a.b']``)."""
    if not path:
        return "$"
    label = "$"
    for part in path:
        if isinstance(part, int):
            label += f"[{part}]"
        else:
            safe = str(part).replace("'", "\\'")
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", safe):
                label += f".{safe}"
            else:
                label += f"['{safe}']"
    return label


def _list_path_is_semantic(path: JsonPath) -> bool:
    """Lists linked to object keys (or the root) are splittable; lists inside
    isolated items are not (splitting them produces semantically confusing parts)."""
    return not any(isinstance(part, int) for part in path)


def find_largest_list(data: Any) -> tuple[JsonPath, list[Any]]:
    """Detect the main preservable list.

    Rules (mirror of the legacy GUI):

    - if the root JSON is a list, it is the main list;
    - otherwise the largest list reachable only through object keys wins;
    - lists nested inside a specific item are avoided.
    """
    if isinstance(data, list):
        return (), data

    candidates: list[tuple[JsonPath, list[Any]]] = []

    def walk(obj: Any, path: JsonPath) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                child_path = path + (key,)
                if isinstance(value, list):
                    if _list_path_is_semantic(child_path):
                        candidates.append((child_path, value))
                    for index, item in enumerate(value):
                        if isinstance(item, (dict, list)):
                            walk(item, child_path + (index,))
                elif isinstance(value, dict):
                    walk(value, child_path)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    walk(item, path + (index,))

    walk(data, ())
    if not candidates:
        return (), []
    # Largest list wins; ties favor the shortest path (usually the most "main").
    candidates.sort(key=lambda pair: (len(pair[1]), -len(pair[0])), reverse=True)
    return candidates[0]


def replace_at_path(data: Any, path: JsonPath, value: Any) -> Any:
    """Return a deep copy of ``data`` with the list at ``path`` replaced."""
    if not path:
        return value
    clone = copy.deepcopy(data)
    cursor = clone
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value
    return clone


# ---------------------------------------------------------------------------
# Size estimation (deterministic)
# ---------------------------------------------------------------------------


def estimate_bytes(obj: Any) -> int:
    return len(json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))


def _item_size_estimate(item: Any) -> int:
    # Small allowance for comma, newline and indentation within the list.
    return len(json.dumps(item, ensure_ascii=False, indent=2).encode("utf-8")) + 4


def estimate_chunk_bytes(data: Any, list_path: JsonPath, chunk: Sequence[Any]) -> int:
    """Estimate the on-disk size of one part without serializing the whole
    document per item."""
    try:
        empty_overhead = estimate_bytes(replace_at_path(data, list_path, []))
    except Exception:
        empty_overhead = 2
    return empty_overhead + sum(_item_size_estimate(item) for item in chunk)


# ---------------------------------------------------------------------------
# Split algorithms (the transformation logic)
# ---------------------------------------------------------------------------


def split_evenly(items: Sequence[Any], parts: int) -> list[list[Any]]:
    """Split ``items`` into ``parts`` even chunks (never more chunks than items)."""
    real_parts = min(parts, len(items))
    base = len(items) // real_parts
    remainder = len(items) % real_parts
    chunks: list[list[Any]] = []
    start = 0
    for index in range(real_parts):
        size = base + (1 if index < remainder else 0)
        chunks.append(list(items[start : start + size]))
        start += size
    return chunks


def chunk_by_target_size(
    data: Any,
    list_path: JsonPath,
    items: Sequence[Any],
    target_bytes: int,
) -> list[list[Any]]:
    """Greedily chunk ``items`` so each part stays close to ``target_bytes``."""
    try:
        overhead = estimate_bytes(replace_at_path(data, list_path, []))
    except Exception:
        overhead = 2

    chunks: list[list[Any]] = []
    current: list[Any] = []
    current_size = overhead

    for item in items:
        item_size = _item_size_estimate(item)
        if current and current_size + item_size > target_bytes:
            chunks.append(current)
            current = [item]
            current_size = overhead + item_size
        else:
            current.append(item)
            current_size += item_size

    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------------------
# Document-level split (the capability entry point)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SplitPlan:
    """Deterministic structural plan for one split operation."""

    root_type: str
    list_path: JsonPath
    list_path_label: str
    item_count: int
    chunks: tuple[list[Any], ...]
    estimated_sizes: tuple[int, ...]

    @property
    def part_count(self) -> int:
        return len(self.chunks)


def split_json_document(data: Any, options: SplitOptions) -> SplitPlan:
    """Produce the split plan for ``data`` under validated ``options``.

    This is the capability's core transformation owner: no I/O, deterministic.
    """
    list_path, items = find_largest_list(data)

    if isinstance(data, list):
        if not items:
            raise EmptyMainListError("The root JSON list is empty; nothing to split.")
    elif not items:
        raise NoMainListError(
            "No main list with items was found. The JSON must be a list at the root "
            "or an object containing a main list reachable through object keys."
        )

    if options.mode == "parts":
        chunks = split_evenly(items, options.parts)
    else:
        chunks = chunk_by_target_size(data, list_path, items, options.target_bytes)

    if not chunks:
        if options.mode == "parts":
            raise InvalidPartsError("The split would produce empty parts; check the part count.")
        raise InvalidTargetSizeError(
            "The size split would produce empty parts; increase target_bytes."
        )

    estimated_sizes = tuple(estimate_chunk_bytes(data, list_path, chunk) for chunk in chunks)
    return SplitPlan(
        root_type=type(data).__name__,
        list_path=list_path,
        list_path_label=json_path_label(list_path),
        item_count=len(items),
        chunks=tuple(chunks),
        estimated_sizes=estimated_sizes,
    )
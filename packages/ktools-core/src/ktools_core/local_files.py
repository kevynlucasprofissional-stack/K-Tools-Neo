from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


class LocalFileUriError(ValueError):
    """The supplied URI cannot be treated as a supported local file path."""


def path_from_file_uri(uri: str) -> Path:
    """Resolve a local ``file://`` URI with one cross-platform K-Tools policy.

    V1 accepts ordinary local file URIs plus ``file://localhost/...`` and
    deliberately rejects remote/UNC authorities. Capability-specific callers
    should translate ``LocalFileUriError`` into their own public error taxonomy.
    """
    if not isinstance(uri, str) or not uri:
        raise LocalFileUriError("A non-empty file:// URI is required")

    parsed = urlparse(uri)
    if parsed.scheme.lower() != "file":
        raise LocalFileUriError(
            f"Only local file:// URIs are supported, got: {parsed.scheme or 'no scheme'}"
        )
    if parsed.netloc not in {"", "localhost"}:
        raise LocalFileUriError("Network/UNC file URI authorities are not supported in V1")

    raw_path = url2pathname(unquote(parsed.path))
    if os.name == "nt" and len(raw_path) >= 3 and raw_path[0] in {"/", "\\"} and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return Path(raw_path).resolve()

from __future__ import annotations

import os
import tempfile
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


def local_path_key(path: Path) -> str:
    """Return the stable path-comparison key used by local publication guards."""
    candidate = Path(path)
    try:
        value = str(candidate.expanduser().resolve())
    except Exception:
        try:
            value = str(candidate.absolute())
        except Exception:
            value = str(candidate)
    # Preserve the historical Windows-first collision policy used by legacy
    # K-Tools and the first Text pack extraction.
    return value.casefold()


def same_local_path(left: Path, right: Path) -> bool:
    return local_path_key(left) == local_path_key(right)


def temporary_sibling_path(output_path: Path, *, suffix: str | None = None) -> Path:
    """Reserve a temporary path beside the destination for atomic publication."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(
        prefix=f".{output.stem}_ktools_",
        suffix=output.suffix if suffix is None else suffix,
        dir=str(output.parent),
    )
    os.close(fd)
    return Path(name)


def cleanup_local_path(path: Path) -> None:
    """Best-effort removal for temporary/intermediate local files."""
    candidate = Path(path)
    try:
        candidate.unlink(missing_ok=True)
    except TypeError:  # Python compatibility guard
        if candidate.exists():
            candidate.unlink()
    except OSError:
        pass


def replace_temp_output(temp_path: Path, output_path: Path) -> None:
    """Promote a complete sibling temp file to the requested final destination."""
    temp = Path(temp_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(temp), str(output))

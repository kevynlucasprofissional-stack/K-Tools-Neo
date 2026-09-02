from __future__ import annotations

from pathlib import Path

from ktools_core.models import Artifact, DataType

from . import writer


class TextSplitError(ValueError):
    """Base classified error for balanced MD/TXT split."""


SPLIT_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def _validate_parts(parts: int) -> int:
    if isinstance(parts, bool) or not isinstance(parts, int):
        raise TextSplitError("text split parts must be an integer >= 2")
    if parts < 2:
        raise TextSplitError("text split parts must be at least 2")
    return parts


def _validate_source(input_file: Path) -> Path:
    source = Path(input_file).expanduser()
    if not source.exists():
        raise TextSplitError(f"Text split source does not exist: {source}")
    if not source.is_file():
        raise TextSplitError(f"Text split source is not a file: {source}")
    if source.suffix.lower() not in writer.TEXT_EXTENSIONS:
        raise TextSplitError(f"Text split source must be .md or .txt: {source}")
    return source


def _prepare_output_dir(output_dir: Path) -> Path:
    dest = Path(output_dir).expanduser()
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise TextSplitError(f"Could not create text split output directory {dest}: {exc}") from exc
    if not dest.is_dir():
        raise TextSplitError(f"Text split output path is not a directory: {dest}")
    return dest


def read_text_document_with_fallback(path: Path) -> tuple[str, str]:
    source = Path(path)
    last_error: UnicodeDecodeError | None = None
    for encoding in SPLIT_ENCODINGS:
        try:
            return source.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
        except OSError as exc:
            raise TextSplitError(f"Could not read text split source {source}: {exc}") from exc
    raise TextSplitError(f"Could not decode text split source {source}: {last_error}")


def split_text_balanced(content: str, parts: int) -> list[str]:
    requested_parts = _validate_parts(parts)
    if not isinstance(content, str):
        raise TextSplitError("text split content must be a string")
    if not content:
        raise TextSplitError("Cannot split an empty text document")

    units = content.splitlines(keepends=True)
    if not units:
        units = [content]
    actual_parts = min(requested_parts, max(1, len(units)))
    total_chars = sum(len(unit) for unit in units)
    target = max(1, total_chars / actual_parts)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    remaining_parts = actual_parts

    for index, unit in enumerate(units):
        units_left = len(units) - index
        current.append(unit)
        current_len += len(unit)
        if (
            remaining_parts > 1
            and current_len >= target
            and units_left > remaining_parts - 1
        ):
            chunk = "".join(current)
            if chunk.strip():
                chunks.append(chunk)
            current = []
            current_len = 0
            remaining_parts -= 1
            remaining_chars = sum(len(value) for value in units[index + 1 :])
            if remaining_parts:
                target = max(1, remaining_chars / remaining_parts)

    tail = "".join(current)
    if tail.strip():
        chunks.append(tail)

    chunks = [chunk for chunk in chunks if chunk.strip()]
    if not chunks:
        raise TextSplitError("Text split produced only empty/whitespace parts")
    return chunks


def _candidate_key(path: Path) -> str:
    try:
        value = str(path.resolve())
    except Exception:
        value = str(path.absolute())
    return value.lower()


def _safe_unique_path(path: Path, reserved: set[str]) -> Path:
    candidate = Path(path)
    index = 1
    while True:
        key = _candidate_key(candidate)
        if key not in reserved and not candidate.exists():
            reserved.add(key)
            return candidate
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        index += 1


def split_text_file_into_parts(
    input_file: Path,
    output_dir: Path,
    parts: int,
    progress_callback: writer.ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> list[Artifact]:
    source = _validate_source(Path(input_file))
    requested_parts = _validate_parts(parts)
    dest = _prepare_output_dir(Path(output_dir))
    content, source_encoding = read_text_document_with_fallback(source)
    chunks = split_text_balanced(content, requested_parts)
    total = len(chunks)
    reserved: set[str] = set()
    outputs: list[Artifact] = []

    for index, chunk in enumerate(chunks, start=1):
        clean_path = dest / (
            f"{source.stem}_parte_{index:02d}_de_{total:02d}{source.suffix.lower()}"
        )
        output = _safe_unique_path(clean_path, reserved)
        if progress_callback is not None:
            progress_callback(index, total, f"Saving {source.name} — part {index} of {total}")
        try:
            writer.write_text_content_atomic(
                chunk,
                output,
                encoding="utf-8",
                newline="",
            )
        except TextSplitError:
            raise
        except Exception as exc:
            raise TextSplitError(f"Failed to publish text split part {index}: {exc}") from exc

        mime_type = "text/markdown" if output.suffix.lower() == ".md" else "text/plain"
        outputs.append(
            Artifact.create(
                type=DataType.FILE,
                uri=output.resolve().as_uri(),
                produced_by=produced_by,
                mime_type=mime_type,
                metadata={
                    "sourceName": source.name,
                    "sourceEncoding": source_encoding,
                    "partIndex": index,
                    "partCount": total,
                    "charCount": len(chunk),
                    "lineCount": len(chunk.splitlines()),
                    "format": output.suffix.lower().lstrip("."),
                },
            )
        )
    return outputs

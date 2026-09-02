from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image


class ImagePublicationError(RuntimeError):
    """Raised when an image output cannot be safely published."""


def _candidate_key(path: Path) -> str:
    try:
        value = str(path.resolve())
    except Exception:
        value = str(path.absolute())
    return value.lower()


def prepare_output_dir(output_dir: Path) -> Path:
    destination = Path(output_dir).expanduser()
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ImagePublicationError(f"Could not create image output directory {destination}: {exc}") from exc
    if not destination.is_dir():
        raise ImagePublicationError(f"Image output path is not a directory: {destination}")
    return destination


def reserve_unique_png_path(output_dir: Path, stem: str, reserved: set[str]) -> Path:
    base = Path(output_dir) / f"{stem}.png"
    candidate = base
    index = 1
    while True:
        key = _candidate_key(candidate)
        if key not in reserved and not candidate.exists():
            reserved.add(key)
            return candidate
        candidate = base.with_name(f"{base.stem}_{index}{base.suffix}")
        index += 1


def _temp_png_path(output_path: Path) -> Path:
    fd, name = tempfile.mkstemp(
        prefix=f".{output_path.stem}_ktools_",
        suffix=".png",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(name)
    try:
        temp_path.unlink(missing_ok=True)
    except TypeError:
        if temp_path.exists():
            temp_path.unlink()
    return temp_path


def _cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except TypeError:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
    except OSError:
        pass


def publish_png_atomic(image: Image.Image, output_path: Path) -> Path:
    """Publish one PNG via same-directory temp + replace; the batch itself is not transactional."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _temp_png_path(destination)
    try:
        image.save(temp_path, "PNG")
        if not temp_path.exists() or temp_path.stat().st_size <= 0:
            raise ImagePublicationError(f"PNG writer produced no output for {destination}")
        os.replace(temp_path, destination)
    except ImagePublicationError:
        _cleanup(temp_path)
        raise
    except Exception as exc:
        _cleanup(temp_path)
        raise ImagePublicationError(f"Could not publish PNG {destination}: {exc}") from exc
    return destination

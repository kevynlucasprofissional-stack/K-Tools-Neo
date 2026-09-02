from __future__ import annotations

import warnings
from pathlib import Path

from PIL import Image

from . import safety
from .safety import ImageSafetyError


class ImageDecodeError(RuntimeError):
    """Raised when a supported image cannot be decoded under the shared V1 policy."""


def load_safe_first_frame(image_path: Path) -> tuple[Image.Image, bool, str | None]:
    """Load, orient and detach the first frame of one local image.

    The returned image is caller-owned and remains valid after the source file is closed.
    Safety/bomb policy stays owned by ``ktools_images.safety``; this module owns the
    guarded decode + frame-selection + EXIF orchestration shared by image capabilities.
    """
    source = Path(image_path)
    warning_cls, error_cls = safety.configure_pillow_safety()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", warning_cls)
            with Image.open(source) as opened:
                source_format = str(opened.format) if opened.format else None
                safety.validate_image_size_or_raise(source, opened.size)
                animated = bool(getattr(opened, "is_animated", False))
                if animated:
                    try:
                        opened.seek(0)
                    except Exception as exc:
                        raise ImageDecodeError(
                            f"Could not read first frame from animated image '{source.name}'"
                        ) from exc

                normalized = safety.normalize_orientation(opened)
                try:
                    safety.validate_image_size_or_raise(source, normalized.size)
                    normalized.load()
                    detached = normalized.copy()
                    detached.info.update(dict(normalized.info))
                finally:
                    if normalized is not opened:
                        normalized.close()

        return detached, animated, source_format
    except ImageSafetyError:
        raise
    except (warning_cls, error_cls) as exc:
        raise safety.decompression_bomb_error(source, exc) from exc
    except ImageDecodeError:
        raise
    except Exception as exc:
        raise ImageDecodeError(
            f"Could not decode image '{source.name}'; the file may be corrupt, invalid or unreadable"
        ) from exc

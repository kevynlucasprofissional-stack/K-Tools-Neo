from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

MAX_IMAGE_TOTAL_PIXELS = 80_000_000


class ImageSafetyError(RuntimeError):
    """Raised when an image violates the bounded decode/safety policy."""


def configure_pillow_safety() -> tuple[type[Warning], type[BaseException]]:
    """Apply the pack-owned Pillow bomb ceiling and return Pillow bomb classes."""
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_TOTAL_PIXELS
    warning_cls = getattr(Image, "DecompressionBombWarning", Warning)
    error_cls = getattr(Image, "DecompressionBombError", RuntimeError)
    return warning_cls, error_cls


def validate_image_size_or_raise(image_path: Path, size: tuple[int, int]) -> None:
    try:
        width, height = int(size[0]), int(size[1])
    except Exception as exc:
        raise ImageSafetyError(f"Could not determine image dimensions for {image_path}") from exc
    if width <= 0 or height <= 0:
        raise ImageSafetyError(f"Image has invalid dimensions: {image_path} ({width}x{height})")
    pixels = width * height
    if pixels > MAX_IMAGE_TOTAL_PIXELS:
        raise ImageSafetyError(
            f"Image is blocked by the K-Tools safety limit: {image_path.name} "
            f"has {pixels} pixels, limit is {MAX_IMAGE_TOTAL_PIXELS}"
        )


def normalize_orientation(image: Image.Image) -> Image.Image:
    """Return an EXIF-orientation-normalized image."""
    return ImageOps.exif_transpose(image)


def decompression_bomb_error(image_path: Path, exc: BaseException) -> ImageSafetyError:
    return ImageSafetyError(
        f"Image '{image_path.name}' was blocked because it is too large or resembles a decompression bomb"
    )

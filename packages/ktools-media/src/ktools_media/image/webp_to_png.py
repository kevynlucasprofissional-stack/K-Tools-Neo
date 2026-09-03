"""WebP to PNG conversion capability."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover – Pillow is a runtime dep
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


def webp_to_png(input_path: Path, output_path: Path) -> Path:
    """
    Converts a single WebP image to PNG using Pillow.
    Handles animated WebPs by extracting only the first frame.
    Preserves transparency.
    Writes atomically via a .tmp file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = output_path.with_name(f"{output_path.name}.{uuid4().hex}.tmp")

    try:
        if Image is None or ImageOps is None:
            raise RuntimeError("Pillow is required for WebP to PNG conversion. Install it with: pip install Pillow")

        with Image.open(input_path) as img:
            # Handle animated WebP - use first frame only
            try:
                img.seek(0)
            except Exception:
                pass

            # Handle EXIF rotation
            img = ImageOps.exif_transpose(img)

            # Ensure RGBA for PNG transparency support
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")

            img.save(str(tmp_out), "PNG")

        os.replace(tmp_out, output_path)
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass

    return output_path

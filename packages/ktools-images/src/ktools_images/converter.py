from __future__ import annotations

import warnings
from pathlib import Path
from typing import Callable, Sequence

from PIL import Image

from ktools_core.models import Artifact, DataType

from . import publication, safety
from .publication import ImagePublicationError
from .safety import ImageSafetyError

ProgressCallback = Callable[[float, str], None]


class ImageConversionError(RuntimeError):
    """Raised when WebP→PNG conversion cannot complete under the V1 contract."""


def _supported_sources(input_files: Sequence[Path]) -> list[Path]:
    if isinstance(input_files, (str, bytes, Path)):
        raise ImageConversionError("WebP conversion requires an ordered sequence of paths")
    sources: list[Path] = []
    for raw in input_files:
        path = Path(raw)
        try:
            if path.is_file() and path.suffix.lower() == ".webp":
                sources.append(path)
        except OSError:
            continue
    if not sources:
        raise ImageConversionError("No compatible WebP files were provided")
    return sources


def _normalize_png_mode(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"}:
        return image.convert("RGBA")
    if image.mode == "P" and "transparency" in image.info:
        return image.convert("RGBA")
    if image.mode in {"RGB", "L"}:
        return image
    return image.convert("RGB")


def convert_webp_files_to_png(
    input_files: Sequence[Path],
    output_dir: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> list[Artifact]:
    """Convert existing WebP files to collision-safe PNG Artifacts in input order."""
    sources = _supported_sources(input_files)
    destination = publication.prepare_output_dir(Path(output_dir))
    warning_cls, error_cls = safety.configure_pillow_safety()
    reserved: set[str] = set()
    outputs: list[Artifact] = []
    total = len(sources)

    for index, source in enumerate(sources, start=1):
        if progress_callback is not None:
            progress_callback((index - 1) / total, f"Converting WebP {index} of {total}: {source.name}")

        output_path = publication.reserve_unique_png_path(destination, source.stem, reserved)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", warning_cls)
                with Image.open(source) as opened:
                    safety.validate_image_size_or_raise(source, opened.size)
                    animated = bool(getattr(opened, "is_animated", False))
                    if animated:
                        try:
                            opened.seek(0)
                        except Exception as exc:
                            raise ImageConversionError(f"Could not read first frame from animated WebP {source}") from exc
                        if progress_callback is not None:
                            progress_callback(
                                (index - 1) / total,
                                f"{source.name}: animated WebP detected; using first frame only",
                            )

                    normalized = safety.normalize_orientation(opened)
                    try:
                        safety.validate_image_size_or_raise(source, normalized.size)
                        normalized.load()
                        prepared = _normalize_png_mode(normalized)
                        try:
                            mode = prepared.mode
                            width, height = prepared.size
                            publication.publish_png_atomic(prepared, output_path)
                        finally:
                            if prepared is not normalized:
                                prepared.close()
                    finally:
                        if normalized is not opened:
                            normalized.close()
        except ImageSafetyError:
            raise
        except (warning_cls, error_cls) as exc:
            raise safety.decompression_bomb_error(source, exc) from exc
        except ImageConversionError:
            raise
        except ImagePublicationError as exc:
            raise ImageConversionError(f"Could not convert '{source.name}' to PNG: {exc}") from exc
        except Exception as exc:
            raise ImageConversionError(
                f"Could not convert '{source.name}' to PNG; the file may be corrupt, invalid or unreadable"
            ) from exc

        outputs.append(
            Artifact.create(
                type=DataType.IMAGE,
                uri=output_path.resolve().as_uri(),
                produced_by=produced_by,
                mime_type="image/png",
                metadata={
                    "sourceName": source.name,
                    "sourceAnimated": animated,
                    "framePolicy": "first",
                    "orientationNormalized": True,
                    "mode": mode,
                    "width": width,
                    "height": height,
                },
            )
        )

        if progress_callback is not None:
            progress_callback(index / total, f"Converted {source.name} to {output_path.name}")

    return outputs

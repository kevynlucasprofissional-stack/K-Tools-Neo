from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from PIL import Image

from ktools_core.models import Artifact, DataType

from . import publication, reader
from .publication import ImagePublicationError
from .safety import ImageSafetyError

ProgressCallback = Callable[[float, str], None]
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class ImagePdfError(RuntimeError):
    """Raised when ordered image sources cannot be published as one PDF."""


def _supported_sources(input_files: Sequence[Path]) -> list[Path]:
    if isinstance(input_files, (str, bytes, Path)):
        raise ImagePdfError("Images→PDF requires an ordered sequence of paths")

    sources: list[Path] = []
    for raw in input_files:
        try:
            path = Path(raw)
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                sources.append(path)
        except (TypeError, OSError):
            continue

    if not sources:
        raise ImagePdfError("No compatible image files were provided")
    return sources


def _ensure_pdf_extension(output_file: Path) -> Path:
    destination = Path(output_file).expanduser()
    if destination.suffix.lower() != ".pdf":
        destination = destination.with_suffix(".pdf")
    return destination


def _prepare_pdf_page(image: Image.Image) -> Image.Image:
    """Return a caller-owned RGB page, compositing transparency on white."""
    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        try:
            background.paste(rgba, mask=alpha)
        finally:
            alpha.close()
            rgba.close()
        return background
    return image.convert("RGB")


def images_to_pdf(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: ProgressCallback | None = None,
    *,
    produced_by: str | None = None,
) -> Artifact:
    """Prepare ordered image pages and atomically publish one aggregate PDF Artifact."""
    sources = _supported_sources(input_files)
    destination = _ensure_pdf_extension(Path(output_file))
    prepared_pages: list[Image.Image] = []
    page_sizes: list[list[int]] = []
    animated_sources: list[str] = []
    total = len(sources)

    try:
        for index, source in enumerate(sources, start=1):
            if progress_callback is not None:
                progress_callback(
                    (index - 1) / total,
                    f"Preparing image {index} of {total}: {source.name}",
                )

            decoded: Image.Image | None = None
            try:
                decoded, animated, _source_format = reader.load_safe_first_frame(source)
                if animated:
                    animated_sources.append(source.name)
                    if progress_callback is not None:
                        progress_callback(
                            (index - 1) / total,
                            f"{source.name}: animated/multi-frame image detected; using first frame only",
                        )
                page = _prepare_pdf_page(decoded)
                prepared_pages.append(page)
                page_sizes.append([int(page.size[0]), int(page.size[1])])
            except ImageSafetyError:
                raise
            except reader.ImageDecodeError as exc:
                raise ImagePdfError(f"Could not prepare image '{source.name}' for PDF: {exc}") from exc
            except ImagePdfError:
                raise
            except Exception as exc:
                raise ImagePdfError(f"Could not prepare image '{source.name}' for PDF") from exc
            finally:
                if decoded is not None:
                    decoded.close()

        if not prepared_pages:
            raise ImagePdfError("No valid image pages were prepared for PDF output")

        if progress_callback is not None:
            progress_callback(0.95, "Saving aggregate image PDF")

        try:
            published = publication.publish_pdf_atomic(prepared_pages, destination)
        except ImagePublicationError as exc:
            raise ImagePdfError(f"Could not publish image PDF '{destination.name}': {exc}") from exc

        artifact = Artifact.create(
            type=DataType.PDF,
            uri=published.resolve().as_uri(),
            produced_by=produced_by,
            mime_type="application/pdf",
            metadata={
                "sourceCount": len(sources),
                "pageCount": len(prepared_pages),
                "sourceNames": [source.name for source in sources],
                "pageSizes": page_sizes,
                "outputMode": "RGB",
                "alphaBackground": "white",
                "orientationNormalized": True,
                "framePolicy": "first",
                "animatedSources": animated_sources,
            },
        )

        if progress_callback is not None:
            progress_callback(1.0, f"Generated PDF with {len(prepared_pages)} image page(s)")
        return artifact
    finally:
        for page in prepared_pages:
            try:
                page.close()
            except Exception:
                pass

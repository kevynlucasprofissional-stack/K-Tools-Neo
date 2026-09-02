from __future__ import annotations

import importlib
import inspect
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine, WorkflowExecutionError
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry

from ktools_images import api, converter, node, publication, safety
from ktools_images.safety import ImageSafetyError


def make_image(
    path: Path,
    *,
    fmt: str | None = None,
    mode: str = "RGB",
    size: tuple[int, int] = (12, 8),
    color=(10, 20, 30),
    exif_orientation: int | None = None,
) -> None:
    image = Image.new(mode, size, color)
    exif = None
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[274] = exif_orientation
    kwargs = {}
    if fmt == "WEBP":
        kwargs["lossless"] = True
    if exif is not None:
        kwargs["exif"] = exif
    try:
        image.save(path, fmt, **kwargs)
    finally:
        image.close()


def make_animated_webp(path: Path) -> None:
    first = Image.new("RGBA", (8, 6), (255, 0, 0, 128))
    second = Image.new("RGBA", (8, 6), (0, 255, 0, 255))
    try:
        first.save(
            path,
            "WEBP",
            save_all=True,
            append_images=[second],
            duration=100,
            loop=0,
            lossless=True,
        )
    finally:
        first.close()
        second.close()


def pdf_page_ratios(path: Path) -> list[float]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    ratios: list[float] = []
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        ratios.append(width / height)
    return ratios


class ImagesToPdfV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _product():
        reader = importlib.import_module("ktools_images.reader")
        pdf_writer = importlib.import_module("ktools_images.pdf_writer")
        node_module = importlib.import_module("ktools_images.node")
        return reader, pdf_writer, node_module

    @classmethod
    def _registry(cls) -> NodeRegistry:
        _, _, node_module = cls._product()
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        node_module.register_nodes(registry)
        return registry

    @classmethod
    def _workflow(cls, paths: list[Path], output_file: Path) -> WorkflowDefinition:
        _, _, node_module = cls._product()
        return WorkflowDefinition(
            id="images-to-pdf-v1",
            nodes=(
                WorkflowNode(
                    id="source",
                    type="files.literal",
                    config={"paths": [str(path) for path in paths]},
                ),
                WorkflowNode(
                    id="pdf",
                    type=node_module.IMAGES_TO_PDF_NODE_TYPE_ID,
                    config={"output_file": str(output_file)},
                ),
            ),
            edges=(
                WorkflowEdge(
                    source_node="source",
                    source_port="files",
                    target_node="pdf",
                    target_port="files",
                ),
            ),
        )

    def test_expected_shared_reader_and_pdf_writer_contracts_exist(self) -> None:
        reader, pdf_writer, node_module = self._product()
        self.assertTrue(callable(reader.load_safe_first_frame))
        self.assertTrue(callable(pdf_writer.images_to_pdf))
        self.assertTrue(hasattr(pdf_writer, "ImagePdfError"))
        self.assertEqual(node_module.IMAGES_TO_PDF_NODE_TYPE_ID, "image.files_to_pdf")
        self.assertTrue(callable(api.images_to_pdf))

    def test_filters_supported_formats_preserves_order_and_returns_pdf_artifact(self) -> None:
        _, pdf_writer, _ = self._product()
        cases = [
            ("a.JPG", "JPEG"),
            ("b.jpeg", "JPEG"),
            ("c.PNG", "PNG"),
            ("d.webp", "WEBP"),
            ("e.BMP", "BMP"),
            ("f.tif", "TIFF"),
            ("g.TIFF", "TIFF"),
        ]
        paths: list[Path] = []
        for index, (name, fmt) in enumerate(cases, start=1):
            path = self.root / name
            make_image(path, fmt=fmt, size=(10 + index, 8), color=(index, index + 1, index + 2))
            paths.append(path)
        ignored = self.root / "ignored.txt"
        ignored.write_text("x", encoding="utf-8")
        missing = self.root / "missing.png"

        artifact = pdf_writer.images_to_pdf(
            [ignored, paths[0], missing, *paths[1:]],
            self.root / "book",
            produced_by="run/node",
        )

        output = path_from_file_uri(artifact.uri)
        self.assertEqual(output.suffix.lower(), ".pdf")
        self.assertTrue(output.exists())
        self.assertGreater(output.stat().st_size, 0)
        self.assertIs(artifact.type, DataType.PDF)
        self.assertEqual(artifact.mime_type, "application/pdf")
        self.assertEqual(artifact.produced_by, "run/node")
        self.assertEqual(artifact.metadata["sourceNames"], [path.name for path in paths])
        self.assertEqual(artifact.metadata["sourceCount"], len(paths))
        self.assertEqual(artifact.metadata["pageCount"], len(paths))
        self.assertEqual(len(pdf_page_ratios(output)), len(paths))

    def test_no_compatible_sources_fails_closed(self) -> None:
        _, pdf_writer, _ = self._product()
        ignored = self.root / "ignored.txt"
        ignored.write_text("x", encoding="utf-8")
        with self.assertRaises(pdf_writer.ImagePdfError):
            pdf_writer.images_to_pdf([ignored, self.root / "missing.png"], self.root / "out.pdf")

    def test_pdf_page_order_matches_input_order_semantically(self) -> None:
        _, pdf_writer, _ = self._product()
        first = self.root / "first.png"
        second = self.root / "second.png"
        third = self.root / "third.png"
        make_image(first, fmt="PNG", size=(10, 20))
        make_image(second, fmt="PNG", size=(30, 10))
        make_image(third, fmt="PNG", size=(5, 40))

        artifact = pdf_writer.images_to_pdf([first, second, third], self.root / "ordered.pdf")
        ratios = pdf_page_ratios(path_from_file_uri(artifact.uri))

        self.assertEqual(len(ratios), 3)
        for actual, expected in zip(ratios, [0.5, 3.0, 0.125]):
            self.assertTrue(math.isclose(actual, expected, rel_tol=0.03, abs_tol=0.03))
        self.assertEqual(artifact.metadata["pageSizes"], [[10, 20], [30, 10], [5, 40]])

    def test_rgba_and_palette_transparency_are_composited_to_white_rgb(self) -> None:
        _, pdf_writer, _ = self._product()
        rgba = Image.new("RGBA", (2, 1), (255, 0, 0, 128))
        palette = Image.new("P", (2, 1))
        palette.putpalette([255, 0, 0, 0, 255, 0] + [0, 0, 0] * 254)
        palette.putdata([0, 1])
        palette.info["transparency"] = 0
        try:
            prepared_rgba = pdf_writer._prepare_pdf_page(rgba)
            prepared_palette = pdf_writer._prepare_pdf_page(palette)
            try:
                self.assertEqual(prepared_rgba.mode, "RGB")
                self.assertEqual(prepared_rgba.getpixel((0, 0)), (255, 127, 127))
                self.assertEqual(prepared_palette.mode, "RGB")
                self.assertEqual(prepared_palette.getpixel((0, 0)), (255, 255, 255))
                self.assertEqual(prepared_palette.getpixel((1, 0)), (0, 255, 0))
            finally:
                prepared_rgba.close()
                prepared_palette.close()
        finally:
            rgba.close()
            palette.close()

    def test_exif_orientation_and_first_frame_are_shared_reader_policy(self) -> None:
        reader, pdf_writer, _ = self._product()
        oriented = self.root / "oriented.jpg"
        animated = self.root / "animated.webp"
        make_image(oriented, fmt="JPEG", size=(8, 12), exif_orientation=6)
        make_animated_webp(animated)

        decoded, animated_flag, source_format = reader.load_safe_first_frame(oriented)
        try:
            self.assertEqual(decoded.size, (12, 8))
            self.assertFalse(animated_flag)
            self.assertEqual(source_format, "JPEG")
        finally:
            decoded.close()

        artifact = pdf_writer.images_to_pdf([oriented, animated], self.root / "out.pdf")
        self.assertEqual(artifact.metadata["pageSizes"], [[12, 8], [8, 6]])
        self.assertEqual(artifact.metadata["framePolicy"], "first")
        self.assertIn("animated.webp", artifact.metadata["animatedSources"])
        self.assertEqual(artifact.metadata["outputMode"], "RGB")
        self.assertEqual(artifact.metadata["alphaBackground"], "white")
        self.assertTrue(artifact.metadata["orientationNormalized"])

    def test_shared_safety_limit_blocks_pdf_before_publication(self) -> None:
        _, pdf_writer, _ = self._product()
        source = self.root / "small.png"
        make_image(source, fmt="PNG", size=(3, 2))
        old_pillow_limit = Image.MAX_IMAGE_PIXELS
        try:
            with mock.patch.object(safety, "MAX_IMAGE_TOTAL_PIXELS", 4):
                with self.assertRaises(ImageSafetyError):
                    pdf_writer.images_to_pdf([source], self.root / "out.pdf")
        finally:
            Image.MAX_IMAGE_PIXELS = old_pillow_limit
        self.assertFalse((self.root / "out.pdf").exists())

    def test_corrupt_later_source_preserves_existing_destination_and_cleans_temp(self) -> None:
        _, pdf_writer, _ = self._product()
        good = self.root / "good.png"
        bad = self.root / "bad.png"
        make_image(good, fmt="PNG")
        bad.write_bytes(b"not an image")
        output = self.root / "existing.pdf"
        output.write_bytes(b"sentinel-pdf")

        with self.assertRaises(pdf_writer.ImagePdfError):
            pdf_writer.images_to_pdf([good, bad], output)

        self.assertEqual(output.read_bytes(), b"sentinel-pdf")
        leftovers = [path for path in self.root.iterdir() if path.name.startswith(".existing") and "ktools" in path.name]
        self.assertEqual(leftovers, [])

    def test_serializer_failure_preserves_destination_and_cleans_temp(self) -> None:
        image = Image.new("RGB", (4, 4), (1, 2, 3))
        output = self.root / "existing.pdf"
        output.write_bytes(b"old")
        try:
            with mock.patch.object(Image.Image, "save", side_effect=OSError("boom")):
                with self.assertRaises(publication.ImagePublicationError):
                    publication.publish_pdf_atomic([image], output)
        finally:
            image.close()
        self.assertEqual(output.read_bytes(), b"old")
        leftovers = [path for path in self.root.iterdir() if path.name.startswith(".existing") and "ktools" in path.name]
        self.assertEqual(leftovers, [])

    def test_node_contract_is_file_set_to_pdf_version_one_never(self) -> None:
        _, _, node_module = self._product()
        definition = self._registry().definition(node_module.IMAGES_TO_PDF_NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["pdf"].type, DataType.PDF)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_workflow_publishes_pdf_artifact_with_registry_snapshot(self) -> None:
        source = self.root / "source.png"
        make_image(source, fmt="PNG")
        workflow = self._workflow([source], self.root / "workflow.pdf")

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), artifact_registry=artifacts).execute(workflow)
            records = artifacts.list_for_run(result.run_id)

        artifact = result.node_outputs["pdf"]["pdf"]
        self.assertIs(artifact.type, DataType.PDF)
        self.assertEqual(artifact.produced_by, f"{result.run_id}/pdf")
        pdf_records = [record for record in records if record.node_id == "pdf" and record.output_port == "pdf"]
        self.assertEqual(len(pdf_records), 1)
        self.assertIsNotNone(pdf_records[0].snapshot)

    def test_cached_files_literal_does_not_suppress_pdf_publication(self) -> None:
        source = self.root / "source.png"
        make_image(source, fmt="PNG")
        output = self.root / "cached.pdf"
        workflow = self._workflow([source], output)
        cache_path = self.root / "cache.sqlite3"

        with SQLiteNodeCache(cache_path) as cache:
            first = WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        first_id = first.node_outputs["pdf"]["pdf"].id

        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            second = WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)
        second_id = second.node_outputs["pdf"]["pdf"].id

        self.assertNotEqual(first_id, second_id)
        self.assertTrue(output.exists())
        pairs = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), pairs)
        self.assertIn(("pdf", RunEventType.NODE_STARTED), pairs)
        self.assertIn(("pdf", RunEventType.NODE_SUCCEEDED), pairs)
        self.assertNotIn(("pdf", RunEventType.NODE_CACHED), pairs)

    def test_direct_api_and_workflow_are_semantically_equivalent(self) -> None:
        _, _, _ = self._product()
        first = self.root / "first.png"
        second = self.root / "second.png"
        make_image(first, fmt="PNG", size=(10, 20))
        make_image(second, fmt="PNG", size=(30, 10), mode="RGBA", color=(20, 40, 60, 100))

        direct = api.images_to_pdf([first, second], self.root / "direct.pdf")
        workflow = WorkflowEngine(self._registry()).execute(
            self._workflow([first, second], self.root / "workflow.pdf")
        )
        node_artifact = workflow.node_outputs["pdf"]["pdf"]

        self.assertEqual(pdf_page_ratios(path_from_file_uri(direct.uri)), pdf_page_ratios(path_from_file_uri(node_artifact.uri)))
        self.assertEqual(dict(direct.metadata), dict(node_artifact.metadata))
        self.assertEqual(direct.mime_type, node_artifact.mime_type)
        self.assertIs(direct.type, node_artifact.type)

    def test_shared_reader_is_single_decode_exif_owner_and_adapters_are_thin(self) -> None:
        reader, pdf_writer, _ = self._product()
        reader_source = inspect.getsource(reader)
        converter_source = inspect.getsource(converter)
        writer_source = inspect.getsource(pdf_writer)
        api_source = inspect.getsource(api)
        node_source = inspect.getsource(node)

        self.assertIn("Image.open", reader_source)
        self.assertIn("safety.normalize_orientation", reader_source)
        self.assertIn("reader.load_safe_first_frame", converter_source)
        self.assertIn("reader.load_safe_first_frame", writer_source)
        for source in (converter_source, writer_source):
            self.assertNotIn("Image.open(", source)
            self.assertNotIn("exif_transpose(", source)
            self.assertNotIn("warnings.simplefilter", source)
        self.assertIn("pdf_writer.images_to_pdf", api_source)
        self.assertIn("pdf_writer.images_to_pdf", node_source)
        forbidden_adapter_tokens = (
            "Image.open(",
            "exif_transpose(",
            "Image.new(",
            ".save(",
            "os.replace(",
            "mkstemp(",
        )
        for token in forbidden_adapter_tokens:
            self.assertNotIn(token, api_source)
            self.assertNotIn(token, node_source)

    def test_bad_source_workflow_failure_is_correlated_to_pdf_node(self) -> None:
        bad = self.root / "bad.png"
        bad.write_bytes(b"broken")
        with self.assertRaises(WorkflowExecutionError) as caught:
            WorkflowEngine(self._registry()).execute(self._workflow([bad], self.root / "out.pdf"))
        self.assertIn("pdf", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

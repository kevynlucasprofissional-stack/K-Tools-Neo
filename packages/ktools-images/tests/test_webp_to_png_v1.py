from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageOps

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine, WorkflowExecutionError
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry

from ktools_images import api, converter, node, publication, safety
from ktools_images.converter import ImageConversionError, convert_webp_files_to_png
from ktools_images.node import WEBP_TO_PNG_NODE_TYPE_ID, register_nodes
from ktools_images.safety import ImageSafetyError


def make_webp(
    path: Path,
    *,
    mode: str = "RGB",
    size: tuple[int, int] = (3, 2),
    color=(10, 20, 30),
    exif_orientation: int | None = None,
) -> None:
    image = Image.new(mode, size, color)
    exif = None
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[274] = exif_orientation
    kwargs = {"lossless": True}
    if exif is not None:
        kwargs["exif"] = exif
    image.save(path, "WEBP", **kwargs)
    image.close()


def make_animated_webp(path: Path) -> None:
    first = Image.new("RGBA", (2, 2), (255, 0, 0, 128))
    second = Image.new("RGBA", (2, 2), (0, 255, 0, 64))
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


def open_snapshot(path: Path) -> tuple[str, tuple[int, int], list[tuple[int, ...] | int]]:
    with Image.open(path) as image:
        image.load()
        return image.mode, image.size, list(image.getdata())


class WebpToPngV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _registry() -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        register_nodes(registry)
        return registry

    @staticmethod
    def _workflow(paths: list[Path], output_dir: Path) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="webp-to-png-v1",
            nodes=(
                WorkflowNode(
                    id="source",
                    type="files.literal",
                    config={"paths": [str(path) for path in paths]},
                ),
                WorkflowNode(
                    id="convert",
                    type=WEBP_TO_PNG_NODE_TYPE_ID,
                    config={"output_dir": str(output_dir)},
                ),
            ),
            edges=(
                WorkflowEdge(
                    source_node="source",
                    source_port="files",
                    target_node="convert",
                    target_port="files",
                ),
            ),
        )

    def test_filters_existing_webp_inputs_preserves_order_and_returns_image_artifacts(self) -> None:
        first = self.root / "first.webp"
        second = self.root / "SECOND.WEBP"
        make_webp(first, color=(10, 20, 30))
        make_webp(second, color=(40, 50, 60))
        ignored = self.root / "ignored.txt"
        ignored.write_text("x", encoding="utf-8")
        missing = self.root / "missing.webp"

        outputs = convert_webp_files_to_png(
            [ignored, first, missing, second],
            self.root / "out",
            produced_by="run/node",
        )

        self.assertEqual([path_from_file_uri(a.uri).name for a in outputs], ["first.png", "SECOND.png"])
        self.assertTrue(all(a.type is DataType.IMAGE for a in outputs))
        self.assertTrue(all(a.mime_type == "image/png" for a in outputs))
        self.assertTrue(all(a.produced_by == "run/node" for a in outputs))
        self.assertEqual([a.metadata["sourceName"] for a in outputs], ["first.webp", "SECOND.WEBP"])

    def test_no_compatible_inputs_fails_closed(self) -> None:
        ignored = self.root / "x.txt"
        ignored.write_text("x", encoding="utf-8")
        with self.assertRaises(ImageConversionError):
            convert_webp_files_to_png([ignored, self.root / "missing.webp"], self.root / "out")

    def test_rgb_and_alpha_semantics_are_preserved_in_real_png(self) -> None:
        rgb = self.root / "rgb.webp"
        rgba = self.root / "alpha.webp"
        make_webp(rgb, mode="RGB", color=(11, 22, 33))
        make_webp(rgba, mode="RGBA", color=(100, 120, 140, 77))

        outputs = convert_webp_files_to_png([rgb, rgba], self.root / "out")
        rgb_mode, rgb_size, rgb_pixels = open_snapshot(path_from_file_uri(outputs[0].uri))
        alpha_mode, alpha_size, alpha_pixels = open_snapshot(path_from_file_uri(outputs[1].uri))

        self.assertEqual((rgb_mode, rgb_size), ("RGB", (3, 2)))
        self.assertEqual(set(rgb_pixels), {(11, 22, 33)})
        self.assertEqual((alpha_mode, alpha_size), ("RGBA", (3, 2)))
        self.assertEqual(set(alpha_pixels), {(100, 120, 140, 77)})
        self.assertEqual(outputs[1].metadata["mode"], "RGBA")

    def test_exif_orientation_is_normalized_before_png_publication(self) -> None:
        source = self.root / "oriented.webp"
        image = Image.new("RGB", (2, 3))
        pixels = image.load()
        colors = [
            (255, 0, 0), (0, 255, 0),
            (0, 0, 255), (255, 255, 0),
            (0, 255, 255), (255, 0, 255),
        ]
        index = 0
        for y in range(3):
            for x in range(2):
                pixels[x, y] = colors[index]
                index += 1
        exif = Image.Exif()
        exif[274] = 6
        image.save(source, "WEBP", lossless=True, exif=exif)
        image.close()

        [artifact] = convert_webp_files_to_png([source], self.root / "out")
        mode, size, output_pixels = open_snapshot(path_from_file_uri(artifact.uri))

        self.assertEqual(mode, "RGB")
        self.assertEqual(size, (3, 2))
        with Image.open(source) as opened:
            expected = ImageOps.exif_transpose(opened)
            expected.load()
            expected_pixels = list(expected.getdata())
            expected.close()
        self.assertEqual(output_pixels, expected_pixels)
        self.assertEqual((artifact.metadata["width"], artifact.metadata["height"]), (3, 2))
        self.assertTrue(artifact.metadata["orientationNormalized"])

    def test_animated_webp_uses_first_frame_only_and_records_policy(self) -> None:
        source = self.root / "animated.webp"
        make_animated_webp(source)

        [artifact] = convert_webp_files_to_png([source], self.root / "out")
        mode, size, pixels = open_snapshot(path_from_file_uri(artifact.uri))

        self.assertEqual((mode, size), ("RGBA", (2, 2)))
        self.assertEqual(set(pixels), {(255, 0, 0, 128)})
        self.assertTrue(artifact.metadata["sourceAnimated"])
        self.assertEqual(artifact.metadata["framePolicy"], "first")

    def test_progress_is_bounded_reports_animation_and_finishes_at_one(self) -> None:
        first = self.root / "first.webp"
        animated = self.root / "animated.webp"
        make_webp(first)
        make_animated_webp(animated)
        events: list[tuple[float, str]] = []

        outputs = convert_webp_files_to_png(
            [first, animated],
            self.root / "out",
            lambda value, message: events.append((value, message)),
        )

        self.assertEqual(len(outputs), 2)
        self.assertTrue(events)
        self.assertTrue(all(0.0 <= value <= 1.0 for value, _ in events))
        self.assertEqual(events[-1][0], 1.0)
        self.assertTrue(any("anim" in message.lower() or "frame" in message.lower() for _, message in events))

    def test_safety_limit_is_fail_closed_without_huge_fixture(self) -> None:
        source = self.root / "small.webp"
        make_webp(source, size=(3, 2))
        old_pillow_limit = Image.MAX_IMAGE_PIXELS
        try:
            with mock.patch.object(safety, "MAX_IMAGE_TOTAL_PIXELS", 4):
                with self.assertRaises(ImageSafetyError):
                    convert_webp_files_to_png([source], self.root / "out")
        finally:
            Image.MAX_IMAGE_PIXELS = old_pillow_limit
        self.assertFalse((self.root / "out" / "small.png").exists())

    def test_collision_safe_names_never_overwrite_existing_png(self) -> None:
        source = self.root / "same.webp"
        make_webp(source, color=(1, 2, 3))
        out = self.root / "out"
        out.mkdir()
        existing = out / "same.png"
        existing.write_bytes(b"sentinel")

        first = convert_webp_files_to_png([source], out)
        second = convert_webp_files_to_png([source], out)

        self.assertEqual(existing.read_bytes(), b"sentinel")
        self.assertEqual(path_from_file_uri(first[0].uri).name, "same_1.png")
        self.assertEqual(path_from_file_uri(second[0].uri).name, "same_2.png")

    def test_later_source_failure_keeps_earlier_completed_png_and_cleans_current_temp(self) -> None:
        good = self.root / "good.webp"
        bad = self.root / "bad.webp"
        make_webp(good, color=(9, 8, 7))
        bad.write_bytes(b"not-webp")
        out = self.root / "out"

        with self.assertRaises(ImageConversionError):
            convert_webp_files_to_png([good, bad], out)

        self.assertTrue((out / "good.png").exists())
        self.assertFalse((out / "bad.png").exists())
        leftovers = [path for path in out.iterdir() if path.name.startswith(".bad") or "ktools" in path.name]
        self.assertEqual(leftovers, [])

    def test_node_contract_is_file_set_to_file_set_version_one_never(self) -> None:
        definition = self._registry().definition(WEBP_TO_PNG_NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_workflow_publishes_image_artifacts_with_registry_snapshots(self) -> None:
        first = self.root / "a.webp"
        second = self.root / "b.webp"
        make_webp(first)
        make_webp(second, mode="RGBA", color=(1, 2, 3, 44))

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), artifact_registry=artifacts).execute(
                self._workflow([first, second], self.root / "out")
            )
            records = artifacts.list_for_run(result.run_id)

        outputs = result.node_outputs["convert"]["files"]
        self.assertEqual(len(outputs), 2)
        self.assertTrue(all(item.type is DataType.IMAGE for item in outputs))
        self.assertTrue(all(item.produced_by == f"{result.run_id}/convert" for item in outputs))
        converted = [r for r in records if r.node_id == "convert" and r.output_port == "files"]
        self.assertEqual(len(converted), 2)
        self.assertTrue(all(record.snapshot is not None for record in converted))

    def test_cached_files_literal_does_not_suppress_republication(self) -> None:
        source = self.root / "source.webp"
        make_webp(source)
        workflow = self._workflow([source], self.root / "out")
        cache_path = self.root / "cache.sqlite3"

        with SQLiteNodeCache(cache_path) as cache:
            first = WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            second = WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)

        self.assertEqual(path_from_file_uri(first.node_outputs["convert"]["files"][0].uri).name, "source.png")
        self.assertEqual(path_from_file_uri(second.node_outputs["convert"]["files"][0].uri).name, "source_1.png")
        pairs = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), pairs)
        self.assertIn(("convert", RunEventType.NODE_STARTED), pairs)
        self.assertIn(("convert", RunEventType.NODE_SUCCEEDED), pairs)
        self.assertNotIn(("convert", RunEventType.NODE_CACHED), pairs)

    def test_direct_api_and_workflow_are_pixel_and_metadata_equivalent(self) -> None:
        rgb = self.root / "rgb.webp"
        alpha = self.root / "alpha.webp"
        make_webp(rgb, color=(3, 4, 5))
        make_webp(alpha, mode="RGBA", color=(7, 8, 9, 111))

        direct = api.convert_webp_to_png([rgb, alpha], self.root / "direct")
        workflow = WorkflowEngine(self._registry()).execute(
            self._workflow([rgb, alpha], self.root / "workflow")
        )
        node_outputs = workflow.node_outputs["convert"]["files"]

        self.assertEqual(len(direct), len(node_outputs))
        for left, right in zip(direct, node_outputs):
            self.assertEqual(path_from_file_uri(left.uri).name, path_from_file_uri(right.uri).name)
            self.assertEqual(open_snapshot(path_from_file_uri(left.uri)), open_snapshot(path_from_file_uri(right.uri)))
            left_meta = dict(left.metadata)
            right_meta = dict(right.metadata)
            self.assertEqual(left_meta, right_meta)

    def test_adapter_and_api_delegate_to_one_converter_owner(self) -> None:
        api_source = inspect.getsource(api)
        node_source = inspect.getsource(node)
        converter_source = inspect.getsource(converter)

        self.assertIn("converter.convert_webp_files_to_png", api_source)
        self.assertIn("converter.convert_webp_files_to_png", node_source)
        forbidden_in_adapter = (
            "Image.open(",
            "exif_transpose(",
            ".save(",
            "MAX_IMAGE_PIXELS",
            "DecompressionBomb",
            "mkstemp(",
            "os.replace(",
        )
        for token in forbidden_in_adapter:
            self.assertNotIn(token, api_source)
            self.assertNotIn(token, node_source)
        self.assertIn("Image.open", converter_source)
        self.assertIn("safety.normalize_orientation", converter_source)
        self.assertIn("publication.publish_png_atomic", converter_source)

    def test_workflow_bad_source_is_bound_to_convert_node(self) -> None:
        bad = self.root / "bad.webp"
        bad.write_bytes(b"broken")
        with self.assertRaises(WorkflowExecutionError) as caught:
            WorkflowEngine(self._registry()).execute(self._workflow([bad], self.root / "out"))
        self.assertIn("convert", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

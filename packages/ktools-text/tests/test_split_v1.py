from __future__ import annotations

import importlib
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry

from ktools_text import api, node, writer
from ktools_text.node import register_nodes

SPLIT_NODE_TYPE_ID = "text.split.parts"


def split_module():
    return importlib.import_module("ktools_text.splitter")


def split_api():
    return getattr(api, "split_text_file_into_parts")


class TextSplitV1CharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _registry(self) -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        register_nodes(registry)
        return registry

    @staticmethod
    def _split_workflow(source: Path, output_dir: Path, parts: int = 3) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="text-split",
            nodes=(
                WorkflowNode(id="source", type="file.literal", config={"path": str(source)}),
                WorkflowNode(
                    id="split",
                    type=SPLIT_NODE_TYPE_ID,
                    config={"output_dir": str(output_dir), "parts": parts},
                ),
            ),
            edges=(
                WorkflowEdge(
                    source_node="source",
                    source_port="file",
                    target_node="split",
                    target_port="file",
                ),
            ),
        )

    def test_balanced_planner_preserves_line_units_and_reconstructs_source(self) -> None:
        splitter = split_module()
        split_balanced = getattr(splitter, "split_text_balanced")
        content = "a\nbbbb\ncc\ndddddd\ne\n"

        chunks = split_balanced(content, 3)

        self.assertEqual(chunks, ["a\nbbbb\n", "cc\ndddddd\n", "e\n"])
        self.assertEqual("".join(chunks), content)

    def test_planner_clamps_and_rejects_invalid_or_empty_content(self) -> None:
        splitter = split_module()
        split_balanced = getattr(splitter, "split_text_balanced")
        error_type = getattr(splitter, "TextSplitError")

        self.assertEqual(split_balanced("a\nb\n", 9), ["a\n", "b\n"])
        for bad_parts in (0, 1, True, 2.5, "2"):
            with self.subTest(parts=bad_parts):
                with self.assertRaises(error_type):
                    split_balanced("a\nb\n", bad_parts)
        for empty in ("", "   \n\t\n"):
            with self.subTest(content=repr(empty)):
                with self.assertRaises(error_type):
                    split_balanced(empty, 2)

    def test_split_decoder_prefers_cp1252_before_latin1_without_changing_merge_decoder(self) -> None:
        splitter = split_module()
        read_split = getattr(splitter, "read_text_document_with_fallback")
        source = self.root / "encoding.txt"
        source.write_bytes(b"price=\x80\n")

        text, encoding = read_split(source)

        self.assertEqual(encoding, "cp1252")
        self.assertEqual(text, "price=€\n")
        self.assertEqual(writer.read_text_with_fallback(source), "price=\x80\n")

    def test_direct_file_split_names_utf8_output_normalized_newlines_and_collisions(self) -> None:
        source = self.root / "Notas.TXT"
        source.write_bytes("a\r\nbbbb\r\ncc\r\ndddddd\r\ne\r\n".encode("cp1252"))
        output_dir = self.root / "parts"

        first = split_api()(source, output_dir, 3)
        first_bytes = [path.read_bytes() for path in first]
        second = split_api()(source, output_dir, 3)

        self.assertEqual(
            [path.name for path in first],
            [
                "Notas_parte_01_de_03.txt",
                "Notas_parte_02_de_03.txt",
                "Notas_parte_03_de_03.txt",
            ],
        )
        self.assertEqual(
            [path.name for path in second],
            [
                "Notas_parte_01_de_03_1.txt",
                "Notas_parte_02_de_03_1.txt",
                "Notas_parte_03_de_03_1.txt",
            ],
        )
        self.assertEqual(b"".join(first_bytes).decode("utf-8"), "a\nbbbb\ncc\ndddddd\ne\n")
        self.assertTrue(all(b"\r\n" not in data for data in first_bytes))
        self.assertEqual([path.read_bytes() for path in first], first_bytes)

    def test_direct_split_rejects_bad_source_and_parts(self) -> None:
        splitter = split_module()
        error_type = getattr(splitter, "TextSplitError")
        direct = split_api()
        directory = self.root / "folder"
        directory.mkdir()
        binary = self.root / "image.png"
        binary.write_bytes(b"not text")
        valid = self.root / "valid.md"
        valid.write_text("a\nb\n", encoding="utf-8")

        for bad_source in (self.root / "missing.md", directory, binary):
            with self.subTest(source=bad_source):
                with self.assertRaises(error_type):
                    direct(bad_source, self.root / "bad", 2)
        for bad_parts in (0, 1, True, 2.5, "2"):
            with self.subTest(parts=bad_parts):
                with self.assertRaises(error_type):
                    direct(valid, self.root / "bad-parts", bad_parts)

    def test_progress_is_supplemental_and_reaches_completion(self) -> None:
        source = self.root / "source.md"
        source.write_text("a\nbbbb\ncc\ndddddd\n", encoding="utf-8")
        events: list[tuple[int, int, str]] = []

        outputs = split_api()(
            source,
            self.root / "progress",
            2,
            lambda current, total, message: events.append((current, total, message)),
        )

        self.assertEqual(len(outputs), 2)
        self.assertTrue(events)
        self.assertEqual(events[-1][:2], (2, 2))

    def test_split_node_contract_is_file_to_file_set_and_never_cacheable(self) -> None:
        definition = self._registry().definition(SPLIT_NODE_TYPE_ID)
        self.assertEqual(definition.inputs["file"].type, DataType.FILE)
        self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_workflow_outputs_file_artifacts_with_registry_snapshots(self) -> None:
        source = self.root / "source.md"
        source.write_text("a\nbbbb\ncc\ndddddd\ne\n", encoding="utf-8")
        output_dir = self.root / "parts"

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), artifact_registry=artifacts).execute(
                self._split_workflow(source, output_dir, 3)
            )
            records = artifacts.list_for_run(result.run_id)

        outputs = result.node_outputs["split"]["files"]
        self.assertEqual(len(outputs), 3)
        self.assertTrue(all(isinstance(item, Artifact) for item in outputs))
        self.assertTrue(all(item.type is DataType.FILE for item in outputs))
        self.assertTrue(all(item.mime_type == "text/markdown" for item in outputs))
        self.assertTrue(all(item.produced_by == f"{result.run_id}/split" for item in outputs))
        self.assertEqual([item.metadata["partIndex"] for item in outputs], [1, 2, 3])
        self.assertEqual([item.metadata["partCount"] for item in outputs], [3, 3, 3])
        self.assertTrue(all(item.metadata["sourceEncoding"] == "utf-8-sig" for item in outputs))
        split_records = [record for record in records if record.node_id == "split"]
        self.assertEqual(len(split_records), 3)
        self.assertTrue(all(record.output_port == "files" for record in split_records))
        self.assertTrue(all(record.source == "EXECUTED" for record in split_records))
        self.assertTrue(all(record.snapshot is not None for record in split_records))

    def test_cached_file_literal_does_not_suppress_split_and_second_run_uses_new_names(self) -> None:
        source = self.root / "source.txt"
        source.write_text("a\nbbbb\ncc\ndddddd\n", encoding="utf-8")
        output_dir = self.root / "parts"
        workflow = self._split_workflow(source, output_dir, 2)
        cache_path = self.root / "cache.sqlite3"

        with SQLiteNodeCache(cache_path) as cache:
            first = WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        first_names = [path_from_file_uri(item.uri).name for item in first.node_outputs["split"]["files"]]

        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            second = WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)
        second_names = [path_from_file_uri(item.uri).name for item in second.node_outputs["split"]["files"]]

        pairs = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), pairs)
        self.assertIn(("split", RunEventType.NODE_STARTED), pairs)
        self.assertIn(("split", RunEventType.NODE_SUCCEEDED), pairs)
        self.assertNotIn(("split", RunEventType.NODE_CACHED), pairs)
        self.assertEqual(first_names, ["source_parte_01_de_02.txt", "source_parte_02_de_02.txt"])
        self.assertEqual(second_names, ["source_parte_01_de_02_1.txt", "source_parte_02_de_02_1.txt"])

    def test_direct_and_workflow_are_byte_identical(self) -> None:
        source = self.root / "source.txt"
        source.write_bytes("preço\n€uro\nlinha longa longa\nfim\n".encode("cp1252"))
        direct = split_api()(source, self.root / "direct", 3)
        result = WorkflowEngine(self._registry()).execute(
            self._split_workflow(source, self.root / "workflow", 3)
        )
        workflow_paths = [path_from_file_uri(item.uri) for item in result.node_outputs["split"]["files"]]

        self.assertEqual([path.read_bytes() for path in direct], [path.read_bytes() for path in workflow_paths])

    def test_split_then_merge_composition_uses_ordered_file_set(self) -> None:
        source = self.root / "source.md"
        source.write_text("alpha\nbbbb\ncc\nddddd\nomega\n", encoding="utf-8")
        merged = self.root / "merged.md"
        workflow = WorkflowDefinition(
            id="text-split-merge",
            nodes=(
                WorkflowNode(id="source", type="file.literal", config={"path": str(source)}),
                WorkflowNode(
                    id="split",
                    type=SPLIT_NODE_TYPE_ID,
                    config={"output_dir": str(self.root / "parts"), "parts": 3},
                ),
                WorkflowNode(
                    id="merge",
                    type="text.merge.files",
                    config={"output_path": str(merged), "separator_mode": "nenhum"},
                ),
            ),
            edges=(
                WorkflowEdge(source_node="source", source_port="file", target_node="split", target_port="file"),
                WorkflowEdge(source_node="split", source_port="files", target_node="merge", target_port="files"),
            ),
        )

        result = WorkflowEngine(self._registry()).execute(workflow)
        parts = [path_from_file_uri(item.uri).read_text(encoding="utf-8") for item in result.node_outputs["split"]["files"]]
        self.assertEqual("".join(parts), source.read_text(encoding="utf-8"))
        self.assertEqual(merged.read_text(encoding="utf-8"), "".join(part + "\n\n" for part in parts))

    def test_direct_api_and_node_share_splitter_owner_without_split_logic_in_adapter(self) -> None:
        splitter = split_module()
        direct_source = inspect.getsource(api)
        node_source = inspect.getsource(node)
        self.assertIn("splitter.split_text_file_into_parts", direct_source)
        self.assertIn("splitter.split_text_file_into_parts", node_source)
        split_handler = getattr(node, "_split_parts_handler")
        handler_source = inspect.getsource(split_handler)
        self.assertNotIn("splitlines", handler_source)
        self.assertNotIn("cp1252", handler_source)
        self.assertNotIn("write_text", handler_source)
        self.assertNotIn("_safe_unique_path", handler_source)
        self.assertTrue(callable(getattr(splitter, "split_text_file_into_parts")))

    def test_later_part_failure_keeps_earlier_atomic_part_and_no_failed_destination(self) -> None:
        splitter = split_module()
        error_type = getattr(splitter, "TextSplitError")
        source = self.root / "source.txt"
        output_dir = self.root / "parts"
        source.write_text("a\nbbbb\ncc\ndddddd\n", encoding="utf-8")
        original_publish = writer.write_text_content_atomic
        calls = {"count": 0}

        def fail_second_publish(content, output_path, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise error_type("forced second-part publication failure")
            return original_publish(content, output_path, **kwargs)

        with patch.object(writer, "write_text_content_atomic", side_effect=fail_second_publish):
            with self.assertRaises(error_type):
                splitter.split_text_file_into_parts(source, output_dir, 2)

        first = output_dir / "source_parte_01_de_02.txt"
        second = output_dir / "source_parte_02_de_02.txt"
        self.assertTrue(first.exists())
        self.assertFalse(second.exists())
        self.assertFalse(list(output_dir.glob(".*_ktools_*.tmp")))


if __name__ == "__main__":
    unittest.main()

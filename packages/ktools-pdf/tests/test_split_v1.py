from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.models import Artifact, CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry

from ktools_pdf import api, node
from ktools_pdf.node import register_nodes

SPLIT_NODE_TYPE_ID = "pdf.split.parts"


def make_pdf(path: Path, sizes: list[tuple[float, float]]) -> None:
    writer = PdfWriter()
    try:
        for width, height in sizes:
            writer.add_blank_page(width=width, height=height)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()


def dims(path: Path) -> list[tuple[float, float]]:
    reader = PdfReader(str(path), strict=False)
    try:
        return [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]
    finally:
        stream = getattr(reader, "stream", None)
        close = getattr(stream, "close", None)
        if callable(close):
            close()


def split_api():
    return getattr(api, "split_pdf_into_parts")


class PdfSplitV1CharacterizationTests(unittest.TestCase):
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
            id="pdf-split",
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

    def test_direct_split_balances_contiguous_pages_clamps_and_names_parts(self) -> None:
        source = self.root / "source.pdf"
        make_pdf(source, [(101, 201), (102, 202), (103, 203), (104, 204), (105, 205)])

        outputs = split_api()(source, self.root / "out", 3)
        self.assertEqual([path.name for path in outputs], [
            "source_parte_01_de_03.pdf",
            "source_parte_02_de_03.pdf",
            "source_parte_03_de_03.pdf",
        ])
        self.assertEqual([dims(path) for path in outputs], [
            [(101.0, 201.0), (102.0, 202.0)],
            [(103.0, 203.0), (104.0, 204.0)],
            [(105.0, 205.0)],
        ])

        two_page = self.root / "two.pdf"
        make_pdf(two_page, [(301, 401), (302, 402)])
        clamped = split_api()(two_page, self.root / "clamped", 9)
        self.assertEqual([path.name for path in clamped], [
            "two_parte_01_de_02.pdf",
            "two_parte_02_de_02.pdf",
        ])
        self.assertEqual([len(dims(path)) for path in clamped], [1, 1])

    def test_collision_safe_naming_does_not_overwrite_existing_parts(self) -> None:
        source = self.root / "source.pdf"
        out = self.root / "out"
        make_pdf(source, [(110, 210), (120, 220)])

        first = split_api()(source, out, 2)
        before = [path.read_bytes() for path in first]
        second = split_api()(source, out, 2)

        self.assertEqual([path.name for path in second], [
            "source_parte_01_de_02_1.pdf",
            "source_parte_02_de_02_1.pdf",
        ])
        self.assertEqual([path.read_bytes() for path in first], before)

    def test_invalid_source_parts_empty_and_encrypted_fail_closed(self) -> None:
        directory = self.root / "folder"
        directory.mkdir()
        text = self.root / "notes.txt"
        text.write_text("not pdf", encoding="utf-8")
        valid = self.root / "valid.pdf"
        make_pdf(valid, [(100, 100), (110, 110)])

        for bad_source in (self.root / "missing.pdf", directory, text):
            with self.subTest(source=bad_source):
                with self.assertRaises(Exception):
                    split_api()(bad_source, self.root / "bad-source", 2)

        for bad_parts in (0, 1, True, 2.5, "2"):
            with self.subTest(parts=bad_parts):
                with self.assertRaises(Exception):
                    split_api()(valid, self.root / "bad-parts", bad_parts)

        empty = self.root / "empty.pdf"
        writer = PdfWriter()
        with empty.open("wb") as handle:
            writer.write(handle)
        close = getattr(writer, "close", None)
        if callable(close):
            close()

        encrypted = self.root / "encrypted.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("secret", algorithm="RC4-40")
        with encrypted.open("wb") as handle:
            writer.write(handle)
        close = getattr(writer, "close", None)
        if callable(close):
            close()

        for bad_pdf in (empty, encrypted):
            with self.subTest(pdf=bad_pdf.name):
                with self.assertRaises(Exception):
                    split_api()(bad_pdf, self.root / "protected", 2)

    def test_progress_is_supplemental_and_reaches_completion(self) -> None:
        source = self.root / "source.pdf"
        make_pdf(source, [(101, 201), (102, 202), (103, 203)])
        events: list[tuple[float, str]] = []

        outputs = split_api()(source, self.root / "progress", 2, lambda value, message: events.append((value, message)))

        self.assertEqual(len(outputs), 2)
        self.assertTrue(events)
        self.assertEqual(events[-1][0], 1.0)

    def test_file_literal_and_split_node_contracts_are_cardinality_correct(self) -> None:
        registry = self._registry()
        file_literal = registry.definition("file.literal")
        self.assertEqual(file_literal.outputs["file"].type, DataType.FILE)
        self.assertEqual(file_literal.version, "1")
        self.assertIs(file_literal.cache_policy, CachePolicy.PURE)

        split = registry.definition(SPLIT_NODE_TYPE_ID)
        self.assertEqual(split.inputs["file"].type, DataType.FILE)
        self.assertEqual(split.outputs["files"].type, DataType.FILE_SET)
        self.assertEqual(split.version, "1")
        self.assertIs(split.cache_policy, CachePolicy.NEVER)

    def test_workflow_outputs_pdf_artifacts_with_registry_snapshots(self) -> None:
        source = self.root / "source.pdf"
        output_dir = self.root / "parts"
        make_pdf(source, [(101, 201), (102, 202), (103, 203), (104, 204), (105, 205)])

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), artifact_registry=artifacts).execute(
                self._split_workflow(source, output_dir, 3)
            )
            records = artifacts.list_for_run(result.run_id)

        outputs = result.node_outputs["split"]["files"]
        self.assertEqual(len(outputs), 3)
        self.assertTrue(all(isinstance(item, Artifact) for item in outputs))
        self.assertTrue(all(item.type is DataType.PDF for item in outputs))
        self.assertTrue(all(item.mime_type == "application/pdf" for item in outputs))
        self.assertTrue(all(item.produced_by == f"{result.run_id}/split" for item in outputs))
        self.assertEqual([item.metadata["pageCount"] for item in outputs], [2, 2, 1])
        split_records = [record for record in records if record.node_id == "split"]
        self.assertEqual(len(split_records), 3)
        self.assertTrue(all(record.output_port == "files" for record in split_records))
        self.assertTrue(all(record.source == "EXECUTED" for record in split_records))
        self.assertTrue(all(record.snapshot is not None for record in split_records))

    def test_cached_file_literal_does_not_suppress_split_and_second_run_uses_new_names(self) -> None:
        source = self.root / "source.pdf"
        output_dir = self.root / "parts"
        make_pdf(source, [(100, 200), (110, 210), (120, 220), (130, 230)])
        workflow = self._split_workflow(source, output_dir, 2)
        cache_path = self.root / "cache.sqlite3"

        with SQLiteNodeCache(cache_path) as cache:
            first = WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        first_names = [Path(item.uri).name for item in first.node_outputs["split"]["files"]]

        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            second = WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)
        second_names = [Path(item.uri).name for item in second.node_outputs["split"]["files"]]

        pairs = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), pairs)
        self.assertIn(("split", RunEventType.NODE_STARTED), pairs)
        self.assertIn(("split", RunEventType.NODE_SUCCEEDED), pairs)
        self.assertNotIn(("split", RunEventType.NODE_CACHED), pairs)
        self.assertEqual(first_names, ["source_parte_01_de_02.pdf", "source_parte_02_de_02.pdf"])
        self.assertEqual(second_names, ["source_parte_01_de_02_1.pdf", "source_parte_02_de_02_1.pdf"])

    def test_direct_and_workflow_are_semantically_equivalent(self) -> None:
        source = self.root / "source.pdf"
        make_pdf(source, [(101, 201), (102, 202), (103, 203), (104, 204), (105, 205)])
        direct = split_api()(source, self.root / "direct", 3)
        result = WorkflowEngine(self._registry()).execute(
            self._split_workflow(source, self.root / "workflow", 3)
        )
        workflow_paths = [Path(item.uri.removeprefix("file://")) for item in result.node_outputs["split"]["files"]]

        self.assertEqual([dims(path) for path in direct], [dims(path) for path in workflow_paths])

    def test_split_then_merge_composition_recreates_page_order(self) -> None:
        source = self.root / "source.pdf"
        merged = self.root / "merged.pdf"
        make_pdf(source, [(101, 201), (102, 202), (103, 203), (104, 204), (105, 205)])
        workflow = WorkflowDefinition(
            id="split-merge",
            nodes=(
                WorkflowNode(id="source", type="file.literal", config={"path": str(source)}),
                WorkflowNode(id="split", type=SPLIT_NODE_TYPE_ID, config={"output_dir": str(self.root / "parts"), "parts": 3}),
                WorkflowNode(id="merge", type="pdf.merge.files", config={"output_path": str(merged)}),
            ),
            edges=(
                WorkflowEdge(source_node="source", source_port="file", target_node="split", target_port="file"),
                WorkflowEdge(source_node="split", source_port="files", target_node="merge", target_port="files"),
            ),
        )

        WorkflowEngine(self._registry()).execute(workflow)
        self.assertEqual(dims(merged), dims(source))

    def test_direct_api_and_node_share_splitter_owner_without_page_logic_in_adapter(self) -> None:
        direct_source = inspect.getsource(api)
        node_source = inspect.getsource(node)
        self.assertIn("splitter.split_pdf_into_parts", direct_source)
        self.assertIn("splitter.split_pdf_into_parts", node_source)
        split_handler = getattr(node, "_split_parts_handler")
        handler_source = inspect.getsource(split_handler)
        self.assertNotIn("PdfReader", handler_source)
        self.assertNotIn("PdfWriter", handler_source)
        self.assertNotIn("add_page", handler_source)
        self.assertNotIn("remaining_pages", handler_source)


if __name__ == "__main__":
    unittest.main()

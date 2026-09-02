from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine, WorkflowExecutionError
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_documents import api, batch, node
from ktools_documents.batch import DocumentSplitBatchError, split_documents_into_parts
from ktools_documents.node import DOCUMENT_SPLIT_NODE_TYPE_ID, register_nodes


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


def pdf_dims(path: Path) -> list[tuple[float, float]]:
    reader = PdfReader(str(path), strict=False)
    try:
        return [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]
    finally:
        stream = getattr(reader, "stream", None)
        close = getattr(stream, "close", None)
        if callable(close):
            close()


class DocumentSplitOrchestratorV1Tests(unittest.TestCase):
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
    def _workflow(paths: list[Path], output_dir: Path, parts: int = 2) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="mixed-document-split",
            nodes=(
                WorkflowNode(id="source", type="files.literal", config={"paths": [str(path) for path in paths]}),
                WorkflowNode(id="split", type=DOCUMENT_SPLIT_NODE_TYPE_ID, config={"output_dir": str(output_dir), "parts": parts}),
            ),
            edges=(WorkflowEdge(source_node="source", source_port="files", target_node="split", target_port="files"),),
        )

    def test_batch_filters_supported_inputs_and_flattens_source_then_part_order(self) -> None:
        text = self.root / "alpha.md"
        text.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
        pdf = self.root / "beta.pdf"
        make_pdf(pdf, [(101, 201), (102, 202), (103, 203)])
        unsupported = self.root / "skip.bin"
        unsupported.write_bytes(b"ignored")
        result = split_documents_into_parts([unsupported, text, pdf], self.root / "out", 2, produced_by="run/node")
        self.assertEqual((result.input_count, result.output_count, result.errors), (2, 4, ()))
        self.assertEqual([path_from_file_uri(a.uri).name for a in result.artifacts], [
            "alpha_parte_01_de_02.md", "alpha_parte_02_de_02.md",
            "beta_parte_01_de_02.pdf", "beta_parte_02_de_02.pdf",
        ])
        self.assertEqual([a.type for a in result.artifacts], [DataType.FILE, DataType.FILE, DataType.PDF, DataType.PDF])
        self.assertTrue(all(a.produced_by == "run/node" for a in result.artifacts))

    def test_input_parts_partial_success_and_zero_success_boundaries(self) -> None:
        unsupported = self.root / "skip.bin"
        unsupported.write_bytes(b"x")
        with self.assertRaises(DocumentSplitBatchError):
            split_documents_into_parts([unsupported], self.root / "none", 2)
        for parts in (True, 1, 0, "2", 2.5):
            with self.assertRaises(DocumentSplitBatchError):
                split_documents_into_parts([unsupported], self.root / "none", parts)  # type: ignore[arg-type]

        bad = self.root / "bad.pdf"
        bad.write_bytes(b"broken")
        good = self.root / "later.txt"
        good.write_text("a\nb\nc\nd\n", encoding="utf-8")
        result = split_documents_into_parts([bad, good], self.root / "partial", 2)
        self.assertEqual((result.input_count, result.output_count, len(result.errors)), (2, 2, 1))
        self.assertIn("bad.pdf", result.errors[0])
        self.assertEqual(result.to_report()["errorCount"], 1)
        self.assertEqual([path_from_file_uri(a.uri).name for a in result.artifacts], [
            "later_parte_01_de_02.txt", "later_parte_02_de_02.txt"
        ])

        empty = self.root / "empty.md"
        empty.write_text("  \n", encoding="utf-8")
        with self.assertRaises(DocumentSplitBatchError) as caught:
            split_documents_into_parts([bad, empty], self.root / "bad-only", 2)
        self.assertIn("bad.pdf", str(caught.exception))
        self.assertIn("empty.md", str(caught.exception))

    def test_progress_is_weighted_and_finishes_at_one(self) -> None:
        text = self.root / "a.txt"
        text.write_text("a\nb\nc\nd\n", encoding="utf-8")
        pdf = self.root / "b.pdf"
        make_pdf(pdf, [(100, 200), (110, 210), (120, 220), (130, 230)])
        events: list[tuple[float, str]] = []
        result = split_documents_into_parts([text, pdf], self.root / "out", 2, lambda value, message: events.append((value, message)))
        self.assertEqual(result.output_count, 4)
        values = [value for value, _ in events]
        self.assertTrue(values and all(0.0 <= value <= 1.0 for value in values))
        self.assertEqual(values[-1], 1.0)
        self.assertTrue(any(0.0 < value <= 0.5 for value in values))
        self.assertTrue(any(0.5 <= value <= 1.0 for value in values))

    def test_node_contract_artifacts_registry_and_partial_success_report(self) -> None:
        definition = self._registry().definition(DOCUMENT_SPLIT_NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["report"].type, DataType.JSON)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

        text = self.root / "a.md"
        text.write_text("a\nb\nc\nd\n", encoding="utf-8")
        pdf = self.root / "b.pdf"
        make_pdf(pdf, [(101, 201), (102, 202)])
        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as registry_store:
            result = WorkflowEngine(self._registry(), artifact_registry=registry_store).execute(self._workflow([text, pdf], self.root / "out"))
            records = registry_store.list_for_run(result.run_id)
        outputs = result.node_outputs["split"]["files"]
        report = result.node_outputs["split"]["report"]
        self.assertEqual((report["inputCount"], report["outputCount"], report["errorCount"]), (2, 4, 0))
        self.assertEqual([item.type for item in outputs], [DataType.FILE, DataType.FILE, DataType.PDF, DataType.PDF])
        self.assertTrue(all(item.produced_by == f"{result.run_id}/split" for item in outputs))
        split_records = [r for r in records if r.node_id == "split" and r.output_port == "files"]
        self.assertEqual(len(split_records), 4)
        self.assertTrue(all(r.snapshot is not None for r in split_records))

        bad = self.root / "bad.pdf"
        bad.write_bytes(b"broken")
        partial = WorkflowEngine(self._registry()).execute(self._workflow([bad, text], self.root / "partial"))
        self.assertEqual(partial.node_outputs["split"]["report"]["errorCount"], 1)
        with self.assertRaises(WorkflowExecutionError):
            WorkflowEngine(self._registry()).execute(self._workflow([bad], self.root / "all-bad"))

    def test_cached_source_does_not_suppress_republication(self) -> None:
        text = self.root / "source.txt"
        text.write_text("a\nb\nc\nd\n", encoding="utf-8")
        workflow = self._workflow([text], self.root / "out")
        cache_path = self.root / "cache.sqlite3"
        with SQLiteNodeCache(cache_path) as cache:
            first = WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            second = WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)
        self.assertEqual([path_from_file_uri(a.uri).name for a in first.node_outputs["split"]["files"]], [
            "source_parte_01_de_02.txt", "source_parte_02_de_02.txt"
        ])
        self.assertEqual([path_from_file_uri(a.uri).name for a in second.node_outputs["split"]["files"]], [
            "source_parte_01_de_02_1.txt", "source_parte_02_de_02_1.txt"
        ])
        event_pairs = [(e.node_id, e.event_type) for e in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), event_pairs)
        self.assertIn(("split", RunEventType.NODE_STARTED), event_pairs)
        self.assertNotIn(("split", RunEventType.NODE_CACHED), event_pairs)

    def test_direct_and_workflow_equivalence_ignores_destination_identity(self) -> None:
        text = self.root / "a.txt"
        text.write_text("aa\nbbbb\ncc\ndddd\n", encoding="utf-8")
        pdf = self.root / "b.pdf"
        make_pdf(pdf, [(101, 201), (202, 302), (303, 403)])
        direct = api.split_document_files_into_parts([text, pdf], self.root / "direct", 2)
        workflow_result = WorkflowEngine(self._registry()).execute(self._workflow([text, pdf], self.root / "workflow"))
        workflow_files = workflow_result.node_outputs["split"]["files"]
        workflow_report = workflow_result.node_outputs["split"]["report"]
        direct_report = dict(direct.report)
        direct_folder = Path(str(direct_report.pop("outputFolder")))
        workflow_report_cmp = dict(workflow_report)
        workflow_folder = Path(str(workflow_report_cmp.pop("outputFolder")))
        self.assertEqual(direct_report, workflow_report_cmp)
        self.assertEqual(direct_folder, (self.root / "direct").resolve())
        self.assertEqual(workflow_folder, (self.root / "workflow").resolve())
        self.assertEqual([path_from_file_uri(a.uri).name for a in direct.artifacts], [path_from_file_uri(a.uri).name for a in workflow_files])
        for left, right in zip(direct.artifacts[:2], workflow_files[:2]):
            self.assertEqual(path_from_file_uri(left.uri).read_bytes(), path_from_file_uri(right.uri).read_bytes())
        self.assertEqual([pdf_dims(path_from_file_uri(a.uri)) for a in direct.artifacts[2:]], [pdf_dims(path_from_file_uri(a.uri)) for a in workflow_files[2:]])

    def test_documents_pack_is_orchestration_only(self) -> None:
        source = inspect.getsource(batch)
        self.assertIn("text_splitter.split_text_file_into_parts", source)
        self.assertIn("pdf_splitter.split_pdf_into_parts", source)
        for token in ("PdfReader", "PdfWriter", "add_page", "splitlines(", "SPLIT_ENCODINGS", "write_text_content_atomic", "write_pdf_writer_atomic", "_safe_unique_path"):
            self.assertNotIn(token, source)
        self.assertIn("batch.split_documents_into_parts", inspect.getsource(api))
        self.assertIn("batch.split_documents_into_parts", inspect.getsource(node))


if __name__ == "__main__":
    unittest.main()

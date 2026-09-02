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
from ktools_pdf.node import NODE_TYPE_ID, register_nodes


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
        return [(float(p.mediabox.width), float(p.mediabox.height)) for p in reader.pages]
    finally:
        stream = getattr(reader, "stream", None)
        close = getattr(stream, "close", None)
        if callable(close):
            close()


class PdfMergeNodeCharacterizationTests(unittest.TestCase):
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
    def _workflow(first: Path, second: Path, output: Path) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="pdf-merge",
            nodes=(
                WorkflowNode(id="source", type="files.literal", config={"paths": [str(first), str(second)]}),
                WorkflowNode(id="merge", type=NODE_TYPE_ID, config={"output_path": str(output)}),
            ),
            edges=(
                WorkflowEdge(source_node="source", source_port="files", target_node="merge", target_port="files"),
            ),
        )

    def test_node_contract_is_file_set_to_pdf_and_never_cacheable(self) -> None:
        definition = self._registry().definition(NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["pdf"].type, DataType.PDF)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_workflow_publishes_pdf_artifact_and_registry_occurrence(self) -> None:
        first = self.root / "a.pdf"
        second = self.root / "b.pdf"
        output = self.root / "merged.pdf"
        make_pdf(first, [(101, 201)])
        make_pdf(second, [(301, 401)])

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), artifact_registry=artifacts).execute(
                self._workflow(first, second, output)
            )
            records = artifacts.list_for_run(result.run_id)

        artifact = result.node_outputs["merge"]["pdf"]
        self.assertIsInstance(artifact, Artifact)
        self.assertIs(artifact.type, DataType.PDF)
        self.assertEqual(artifact.produced_by, f"{result.run_id}/merge")
        merge_records = [record for record in records if record.node_id == "merge"]
        self.assertEqual(len(merge_records), 1)
        self.assertEqual(merge_records[0].output_port, "pdf")
        self.assertEqual(merge_records[0].source, "EXECUTED")
        self.assertIsNotNone(merge_records[0].snapshot)
        self.assertEqual(dims(output), [(101.0, 201.0), (301.0, 401.0)])

    def test_merge_executes_again_while_files_literal_may_be_cached(self) -> None:
        first = self.root / "a.pdf"
        second = self.root / "b.pdf"
        output = self.root / "merged.pdf"
        make_pdf(first, [(100, 200)])
        make_pdf(second, [(300, 400)])
        workflow = self._workflow(first, second, output)
        cache_path = self.root / "cache.sqlite3"

        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), cache=cache, journal=journal).execute(workflow)

        event_pairs = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), event_pairs)
        self.assertIn(("merge", RunEventType.NODE_STARTED), event_pairs)
        self.assertIn(("merge", RunEventType.NODE_SUCCEEDED), event_pairs)
        self.assertNotIn(("merge", RunEventType.NODE_CACHED), event_pairs)

    def test_direct_api_and_workflow_are_semantically_equivalent(self) -> None:
        first = self.root / "a.pdf"
        second = self.root / "b.pdf"
        direct = self.root / "direct.pdf"
        workflow_output = self.root / "workflow.pdf"
        make_pdf(first, [(101, 201), (102, 202)])
        make_pdf(second, [(301, 401)])

        api.merge_pdf_files([first, second], direct)
        WorkflowEngine(self._registry()).execute(self._workflow(first, second, workflow_output))

        self.assertEqual(dims(direct), dims(workflow_output))
        self.assertEqual(dims(direct), [(101.0, 201.0), (102.0, 202.0), (301.0, 401.0)])

    def test_direct_api_and_node_share_writer_owner(self) -> None:
        self.assertIn("writer.merge_pdf_files", inspect.getsource(api.merge_pdf_files))
        handler_source = inspect.getsource(node._merge_files_handler)
        self.assertIn("writer.merge_pdf_files", handler_source)
        self.assertNotIn("PdfReader", handler_source)
        self.assertNotIn("PdfWriter", handler_source)
        self.assertNotIn("add_page", handler_source)


if __name__ == "__main__":
    unittest.main()

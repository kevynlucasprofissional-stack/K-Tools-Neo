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


class PdfMergeNodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _pdf(self, name: str, widths: list[float]) -> Path:
        path = self.root / name
        writer = PdfWriter()
        for width in widths:
            writer.add_blank_page(width=width, height=300)
        with path.open("wb") as handle:
            writer.write(handle)
        writer.close()
        return path

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
            edges=(WorkflowEdge(source_node="source", source_port="files", target_node="merge", target_port="files"),),
        )

    def test_node_contract_is_file_set_to_pdf_and_never_cacheable(self) -> None:
        definition = self._registry().definition(NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["pdf"].type, DataType.PDF)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_real_workflow_publishes_pdf_artifact_and_registry_occurrence(self) -> None:
        first = self._pdf("a.pdf", [101])
        second = self._pdf("b.pdf", [201, 202])
        output = self.root / "merged.pdf"
        journal = MemoryRunJournal()

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(self._registry(), journal=journal, artifact_registry=artifacts).execute(
                self._workflow(first, second, output)
            )
            records = artifacts.list_for_run(result.run_id)

        artifact = result.node_outputs["merge"]["pdf"]
        self.assertIsInstance(artifact, Artifact)
        self.assertEqual(artifact.type, DataType.PDF)
        self.assertEqual(artifact.produced_by, f"{result.run_id}/merge")
        self.assertEqual(len(PdfReader(str(output), strict=False).pages), 3)
        merge_records = [record for record in records if record.node_id == "merge"]
        self.assertEqual(len(merge_records), 1)
        self.assertEqual(merge_records[0].output_port, "pdf")
        self.assertEqual(merge_records[0].source, "EXECUTED")
        self.assertIsNotNone(merge_records[0].snapshot)

    def test_merge_executes_again_while_files_literal_may_be_cached(self) -> None:
        first = self._pdf("a.pdf", [101])
        second = self._pdf("b.pdf", [201])
        output = self.root / "merged.pdf"
        workflow = self._workflow(first, second, output)
        cache_path = self.root / "cache.sqlite3"
        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), journal=journal, cache=cache).execute(workflow)

        event_types = [(event.node_id, event.event_type) for event in journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), event_types)
        self.assertIn(("merge", RunEventType.NODE_STARTED), event_types)
        self.assertIn(("merge", RunEventType.NODE_SUCCEEDED), event_types)
        self.assertNotIn(("merge", RunEventType.NODE_CACHED), event_types)

    def test_direct_api_and_workflow_have_same_page_semantics(self) -> None:
        first = self._pdf("a.pdf", [111, 112])
        second = self._pdf("b.pdf", [211])
        direct_output = self.root / "direct.pdf"
        workflow_output = self.root / "workflow.pdf"
        api.merge_pdf_files([first, second], direct_output)
        WorkflowEngine(self._registry()).execute(self._workflow(first, second, workflow_output))

        def widths(path: Path) -> list[int]:
            return [round(float(page.mediabox.width)) for page in PdfReader(str(path), strict=False).pages]

        self.assertEqual(widths(direct_output), widths(workflow_output))
        self.assertEqual(widths(direct_output), [111, 112, 211])

    def test_direct_api_and_workflow_share_writer_owner(self) -> None:
        self.assertIn("writer.merge_pdf_files", inspect.getsource(api.merge_pdf_files))
        handler_source = inspect.getsource(node._merge_files_handler)
        self.assertIn("writer.merge_pdf_files", handler_source)
        self.assertNotIn("PdfReader", handler_source)
        self.assertNotIn("add_page", handler_source)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.models import Artifact, CachePolicy, DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_core.builtin import register_builtin_nodes

from ktools_text import api, node
from ktools_text.node import NODE_TYPE_ID, register_nodes


class TextMergeNodeTests(unittest.TestCase):
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
    def _workflow(first: Path, second: Path, output: Path, mode: str = "nenhum") -> WorkflowDefinition:
        return WorkflowDefinition(
            id="text-merge",
            nodes=(
                WorkflowNode(
                    id="source",
                    type="files.literal",
                    config={"paths": [str(first), str(second)]},
                ),
                WorkflowNode(
                    id="merge",
                    type=NODE_TYPE_ID,
                    config={"output_path": str(output), "separator_mode": mode},
                ),
            ),
            edges=(
                WorkflowEdge(
                    source_node="source",
                    source_port="files",
                    target_node="merge",
                    target_port="files",
                ),
            ),
        )

    def test_node_contract_is_file_set_to_file_and_never_cacheable(self) -> None:
        definition = self._registry().definition(NODE_TYPE_ID)
        self.assertEqual(definition.inputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["file"].type, DataType.FILE)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_real_workflow_publishes_artifact_and_registry_occurrence(self) -> None:
        first = self.root / "a.md"
        second = self.root / "b.txt"
        output = self.root / "merged.md"
        first.write_text("A", encoding="utf-8")
        second.write_text("B", encoding="utf-8")
        journal = MemoryRunJournal()

        with SQLiteArtifactRegistry(self.root / "artifacts.sqlite3") as artifacts:
            result = WorkflowEngine(
                self._registry(),
                journal=journal,
                artifact_registry=artifacts,
            ).execute(self._workflow(first, second, output))
            records = artifacts.list_for_run(result.run_id)

        artifact = result.node_outputs["merge"]["file"]
        self.assertIsInstance(artifact, Artifact)
        self.assertEqual(artifact.produced_by, f"{result.run_id}/merge")
        self.assertEqual(output.read_text(encoding="utf-8"), "A\n\nB\n\n")
        merge_records = [record for record in records if record.node_id == "merge"]
        self.assertEqual(len(merge_records), 1)
        self.assertEqual(merge_records[0].output_port, "file")
        self.assertEqual(merge_records[0].source, "EXECUTED")
        self.assertIsNotNone(merge_records[0].snapshot)

    def test_merge_node_executes_again_while_files_literal_may_be_cached(self) -> None:
        first = self.root / "a.md"
        second = self.root / "b.txt"
        output = self.root / "merged.md"
        first.write_text("A", encoding="utf-8")
        second.write_text("B", encoding="utf-8")
        workflow = self._workflow(first, second, output)
        cache_path = self.root / "cache.sqlite3"
        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), cache=cache).execute(workflow)
        second_journal = MemoryRunJournal()
        with SQLiteNodeCache(cache_path) as cache:
            WorkflowEngine(self._registry(), journal=second_journal, cache=cache).execute(workflow)

        second_types = [(event.node_id, event.event_type) for event in second_journal.events]
        self.assertIn(("source", RunEventType.NODE_CACHED), second_types)
        self.assertIn(("merge", RunEventType.NODE_STARTED), second_types)
        self.assertIn(("merge", RunEventType.NODE_SUCCEEDED), second_types)
        self.assertNotIn(("merge", RunEventType.NODE_CACHED), second_types)

    def test_direct_api_and_workflow_are_byte_identical(self) -> None:
        first = self.root / "a.md"
        second = self.root / "b.txt"
        direct_output = self.root / "direct.md"
        workflow_output = self.root / "workflow.md"
        first.write_text("Árvore", encoding="utf-8")
        second.write_bytes("ação".encode("latin-1"))

        api.merge_text_files([first, second], direct_output, "completo")
        WorkflowEngine(self._registry()).execute(
            self._workflow(first, second, workflow_output, "completo")
        )

        self.assertEqual(direct_output.read_bytes(), workflow_output.read_bytes())

    def test_direct_api_and_workflow_node_share_writer_owner(self) -> None:
        self.assertIn("writer.merge_text_files", inspect.getsource(api.merge_text_files))
        self.assertIn("writer.merge_text_files", inspect.getsource(node._merge_files_handler))
        handler_source = inspect.getsource(node._merge_files_handler)
        self.assertNotIn("render_document_block", handler_source)
        self.assertNotIn("read_text_with_fallback", handler_source)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import Artifact, CachePolicy, DataType, WorkflowDefinition, WorkflowNode
from ktools_core.registry import NodeRegistry


class FileLiteralNodeTests(unittest.TestCase):
    @staticmethod
    def _registry() -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        return registry

    @staticmethod
    def _workflow(path: Path) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="file-literal",
            nodes=(WorkflowNode(id="source", type="file.literal", config={"path": str(path)}),),
            edges=(),
        )

    def test_file_literal_publishes_one_file_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            source.write_text("hello", encoding="utf-8")
            registry = self._registry()
            definition = registry.definition("file.literal")
            self.assertEqual(definition.outputs["file"].type, DataType.FILE)
            self.assertEqual(definition.version, "1")
            self.assertIs(definition.cache_policy, CachePolicy.PURE)

            result = WorkflowEngine(registry).execute(self._workflow(source))
            artifact = result.node_outputs["source"]["file"]
            self.assertIsInstance(artifact, Artifact)
            self.assertIs(artifact.type, DataType.FILE)
            self.assertEqual(path_from_file_uri(artifact.uri), source.resolve())
            self.assertEqual(artifact.metadata["name"], "source.txt")
            self.assertEqual(artifact.produced_by, f"{result.run_id}/source")

    def test_file_literal_rejects_missing_directory_and_empty_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "folder"
            directory.mkdir()
            workflows = (
                WorkflowDefinition(id="empty", nodes=(WorkflowNode(id="source", type="file.literal", config={}),), edges=()),
                self._workflow(Path(temp_dir) / "missing.txt"),
                self._workflow(directory),
            )
            for workflow in workflows:
                with self.subTest(workflow=workflow.id):
                    with self.assertRaises(Exception):
                        WorkflowEngine(self._registry()).execute(workflow)

    def test_file_literal_cache_is_invalidated_by_content_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.txt"
            source.write_text("initial", encoding="utf-8")
            workflow = self._workflow(source)
            cache_path = root / "cache.sqlite3"

            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(self._registry(), cache=cache).execute(workflow)

            cached_journal = MemoryRunJournal()
            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(self._registry(), cache=cache, journal=cached_journal).execute(workflow)
            self.assertIn(RunEventType.NODE_CACHED, [event.event_type for event in cached_journal.events])

            source.write_text("changed-content-longer", encoding="utf-8")
            changed_journal = MemoryRunJournal()
            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(self._registry(), cache=cache, journal=changed_journal).execute(workflow)
            changed_types = [event.event_type for event in changed_journal.events]
            self.assertIn(RunEventType.NODE_STARTED, changed_types)
            self.assertIn(RunEventType.NODE_SUCCEEDED, changed_types)
            self.assertNotIn(RunEventType.NODE_CACHED, changed_types)


if __name__ == "__main__":
    unittest.main()

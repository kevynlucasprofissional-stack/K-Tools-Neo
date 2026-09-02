from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine, WorkflowValidationError
from ktools_core.journal import MemoryRunJournal, RunEventType
from ktools_core.models import (
    Artifact,
    CachePolicy,
    DataType,
    NodeDefinition,
    PortDefinition,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)
from ktools_core.registry import NodeRegistry


class FileSetTypeContractTests(unittest.TestCase):
    def test_file_set_is_an_explicit_ordered_collection_type(self) -> None:
        self.assertEqual(DataType.FILE_SET.value, "file_set")

    def test_file_set_edges_are_exact_in_v1(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.file-set-source",
                title="source",
                outputs={"files": PortDefinition(DataType.FILE_SET)},
            ),
            lambda _inputs, _config, _ctx: {"files": []},
        )
        registry.register(
            NodeDefinition(
                type_id="test.file-set-sink",
                title="sink",
                inputs={"files": PortDefinition(DataType.FILE_SET)},
                outputs={"files": PortDefinition(DataType.FILE_SET)},
            ),
            lambda inputs, _config, _ctx: {"files": inputs["files"]},
        )
        workflow = WorkflowDefinition(
            id="file-set",
            nodes=(
                WorkflowNode(id="source", type="test.file-set-source"),
                WorkflowNode(id="sink", type="test.file-set-sink"),
            ),
            edges=(
                WorkflowEdge(
                    source_node="source",
                    source_port="files",
                    target_node="sink",
                    target_port="files",
                ),
            ),
        )
        self.assertEqual(WorkflowEngine(registry).validate(workflow), ("source", "sink"))

    def test_file_and_file_set_are_not_interchangeable(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.file",
                title="file",
                outputs={"file": PortDefinition(DataType.FILE)},
            ),
            lambda _inputs, _config, _ctx: {"file": None},
        )
        registry.register(
            NodeDefinition(
                type_id="test.files",
                title="files",
                inputs={"files": PortDefinition(DataType.FILE_SET)},
            ),
            lambda inputs, _config, _ctx: {},
        )
        workflow = WorkflowDefinition(
            id="bad-file-set",
            nodes=(
                WorkflowNode(id="one", type="test.file"),
                WorkflowNode(id="many", type="test.files"),
            ),
            edges=(
                WorkflowEdge(
                    source_node="one",
                    source_port="file",
                    target_node="many",
                    target_port="files",
                ),
            ),
        )
        with self.assertRaises(WorkflowValidationError):
            WorkflowEngine(registry).validate(workflow)


class FilesLiteralNodeTests(unittest.TestCase):
    @staticmethod
    def _workflow(paths: list[str]) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="files-literal",
            nodes=(
                WorkflowNode(
                    id="source",
                    type="files.literal",
                    config={"paths": paths},
                ),
            ),
            edges=(),
        )

    @staticmethod
    def _registry() -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        return registry

    def test_files_literal_validates_and_preserves_configured_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.md"
            second = root / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")

            registry = self._registry()
            definition = registry.definition("files.literal")
            self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
            self.assertIs(definition.cache_policy, CachePolicy.PURE)

            result = WorkflowEngine(registry).execute(
                self._workflow([str(second), str(first)])
            )
            files = result.node_outputs["source"]["files"]
            self.assertEqual([Path(item.uri).name for item in files], ["second.txt", "first.md"])
            self.assertTrue(all(isinstance(item, Artifact) for item in files))
            self.assertTrue(all(item.produced_by == f"{result.run_id}/source" for item in files))

    def test_files_literal_rejects_missing_or_empty_paths(self) -> None:
        for paths in ([], ["definitely-missing-ktools-file.txt"]):
            with self.assertRaises(Exception):
                WorkflowEngine(self._registry()).execute(self._workflow(list(paths)))

    def test_files_literal_cache_revalidates_real_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.md"
            source.write_text("initial", encoding="utf-8")
            workflow = self._workflow([str(source)])
            cache_path = root / "cache.sqlite3"

            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(self._registry(), cache=cache).execute(workflow)

            second_journal = MemoryRunJournal()
            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(
                    self._registry(), journal=second_journal, cache=cache
                ).execute(workflow)
            self.assertTrue(
                any(event.event_type is RunEventType.NODE_CACHED for event in second_journal.events)
            )

            source.write_text("changed-content-longer", encoding="utf-8")
            third_journal = MemoryRunJournal()
            with SQLiteNodeCache(cache_path) as cache:
                WorkflowEngine(
                    self._registry(), journal=third_journal, cache=cache
                ).execute(workflow)
            third_types = [event.event_type for event in third_journal.events]
            self.assertIn(RunEventType.NODE_STARTED, third_types)
            self.assertIn(RunEventType.NODE_SUCCEEDED, third_types)
            self.assertNotIn(RunEventType.NODE_CACHED, third_types)


if __name__ == "__main__":
    unittest.main()

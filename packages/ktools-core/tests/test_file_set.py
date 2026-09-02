from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine, WorkflowValidationError
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
    def test_files_literal_validates_and_preserves_configured_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first.md"
            second = root / "second.txt"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")

            registry = NodeRegistry()
            register_builtin_nodes(registry)
            definition = registry.definition("files.literal")
            self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
            self.assertIs(definition.cache_policy, CachePolicy.PURE)

            workflow = WorkflowDefinition(
                id="files-literal",
                nodes=(
                    WorkflowNode(
                        id="source",
                        type="files.literal",
                        config={"paths": [str(second), str(first)]},
                    ),
                ),
                edges=(),
            )
            result = WorkflowEngine(registry).execute(workflow)
            files = result.node_outputs["source"]["files"]
            self.assertEqual([Path(item.uri.removeprefix("file://")).name for item in files], ["second.txt", "first.md"])
            self.assertTrue(all(isinstance(item, Artifact) for item in files))
            self.assertTrue(all(item.produced_by == f"{result.run_id}/source" for item in files))

    def test_files_literal_rejects_missing_or_empty_paths(self) -> None:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        for paths in ([], ["definitely-missing-ktools-file.txt"]):
            workflow = WorkflowDefinition(
                id="bad-files",
                nodes=(WorkflowNode(id="source", type="files.literal", config={"paths": paths}),),
                edges=(),
            )
            with self.assertRaises(Exception):
                WorkflowEngine(registry).execute(workflow)


if __name__ == "__main__":
    unittest.main()

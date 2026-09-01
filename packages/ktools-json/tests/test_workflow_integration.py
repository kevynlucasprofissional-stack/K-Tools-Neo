"""Integration tests through ktools-core's WorkflowEngine.

Prove that the direct API and the workflow node reach the SAME implementation
owner and that the typed contract behaves as declared, including failure
semantics at the engine boundary.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ktools_core import (
    DataType,
    NodeDefinition,
    NodeRegistry,
    PortDefinition,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowExecutionError,
    WorkflowValidationError,
    register_builtin_nodes,
)

from ktools_json import api, node, register_nodes, split_json, writer

RECORDS = {"dataset": "oc001", "records": [{"id": i} for i in range(5)]}


def engine_with_pack() -> WorkflowEngine:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    return WorkflowEngine(registry)


def split_workflow(output_dir: str, **config) -> WorkflowDefinition:
    merged = {"output_dir": output_dir, **config}
    return WorkflowDefinition.from_dict(
        {
            "id": "oc001-split-wf",
            "nodes": [
                {"id": "source", "type": "json.literal", "config": {"value": RECORDS}},
                {"id": "splitter", "type": "json.split", "config": merged},
            ],
            "edges": [
                {
                    "sourceNode": "source",
                    "sourcePort": "json",
                    "targetNode": "splitter",
                    "targetPort": "json_data",
                }
            ],
        }
    )


class WorkflowIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name) / "wf-out"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_workflow_executes_split_node(self) -> None:
        engine = engine_with_pack()
        result = engine.execute(split_workflow(str(self.out), mode="parts", parts=2, prefix="r"))
        splitter = result.node_outputs["splitter"]
        self.assertEqual(splitter["summary"]["partCount"], 2)
        written = sorted(p.name for p in self.out.iterdir())
        self.assertEqual(written, ["r_parte_01_de_02.json", "r_parte_02_de_02.json"])
        self.assertEqual(splitter["summary"]["itemCount"], 5)

    def test_workflow_rejects_incompatible_typed_edge(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.text.jsonish",
                title="Text",
                outputs={"text": PortDefinition(DataType.TEXT)},
            ),
            lambda _i, _c, _ctx: {"text": "{}"},
        )
        registry.register(NodeDefinition(
            type_id="json.split",
            title="Dividir JSON",
            inputs={"json_data": PortDefinition(DataType.JSON)},
            outputs={"parts": PortDefinition(DataType.JSON), "summary": PortDefinition(DataType.JSON)},
        ), lambda _i, _c, _ctx: {"parts": [], "summary": {}})

        workflow = WorkflowDefinition.from_dict(
            {
                "id": "bad-edge",
                "nodes": [
                    {"id": "t", "type": "test.text.jsonish"},
                    {"id": "s", "type": "json.split", "config": {"output_dir": str(self.out)}},
                ],
                "edges": [
                    {"sourceNode": "t", "sourcePort": "text", "targetNode": "s", "targetPort": "json_data"}
                ],
            }
        )
        with self.assertRaisesRegex(WorkflowValidationError, "Incompatible edge"):
            WorkflowEngine(registry).validate(workflow)

    def test_workflow_rejects_missing_required_json_input(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "missing-input",
                "nodes": [
                    {"id": "s", "type": "json.split", "config": {"output_dir": str(self.out)}}
                ],
                "edges": [],
            }
        )
        with self.assertRaisesRegex(WorkflowValidationError, "s.json_data"):
            engine_with_pack().validate(workflow)

    def test_workflow_node_failure_is_bound_to_node(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "bad-config",
                "nodes": [
                    {"id": "source", "type": "json.literal", "config": {"value": RECORDS}},
                    {"id": "splitter", "type": "json.split", "config": {"output_dir": str(self.out), "mode": "nope"}},
                ],
                "edges": [
                    {"sourceNode": "source", "sourcePort": "json", "targetNode": "splitter", "targetPort": "json_data"}
                ],
            }
        )
        with self.assertRaisesRegex(WorkflowExecutionError, "Node splitter failed: .*mode must be"):
            engine_with_pack().execute(workflow)


class SharedOwnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.json"
        self.source.write_text(str(RECORDS).replace("'", '"'), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_direct_and_node_call_the_same_split_and_write(self) -> None:
        """The direct API and the node handler reference the same function."""
        self.assertIs(api.split_and_write, writer.split_and_write)
        self.assertIs(node.split_and_write, writer.split_and_write)

    def test_direct_and_node_reach_same_split_and_write(self) -> None:
        """Both routes must invoke the shared `split_and_write` exactly once each."""
        calls = []

        def recorder(data, options, output_dir, **kwargs):
            calls.append(("split_and_write", options))
            return writer.split_and_write(data, options, output_dir, **kwargs)

        registry = NodeRegistry()
        register_nodes(registry)

        with mock.patch.object(api, "split_and_write", side_effect=recorder), \
                mock.patch.object(node, "split_and_write", side_effect=recorder):
            api.split_json(self.source, self.root / "direct", mode="parts", parts=2)
            registry.execute(
                "json.split",
                {"json_data": RECORDS},
                {"mode": "parts", "parts": 2, "output_dir": str(self.root / "node")},
                None,  # type: ignore[arg-type]
            )

        self.assertEqual(len(calls), 2)
        for _, options in calls:
            self.assertEqual((options.mode, options.parts, options.target_bytes), ("parts", 2, None))

    def test_byte_identical_output_between_direct_and_node(self) -> None:
        """The same input+config produces identical part files via both routes."""
        out_direct = self.root / "d"
        out_node = self.root / "n"

        split_json(self.source, out_direct, mode="parts", parts=2, prefix="r")

        registry = NodeRegistry()
        register_nodes(registry)
        registry.execute(
            "json.split",
            {"json_data": RECORDS},
            {"mode": "parts", "parts": 2, "output_dir": str(out_node), "prefix": "r"},
            None,  # type: ignore[arg-type]
        )

        direct_files = sorted(p.name for p in out_direct.iterdir())
        node_files = sorted(p.name for p in out_node.iterdir())
        self.assertEqual(direct_files, node_files)
        for name in direct_files:
            self.assertEqual(
                (out_direct / name).read_bytes(),
                (out_node / name).read_bytes(),
                f"part {name} diverged between routes",
            )


if __name__ == "__main__":
    unittest.main()
from __future__ import annotations

import unittest

from ktools_core import (
    Artifact,
    DataType,
    NodeDefinition,
    NodeRegistry,
    PortDefinition,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowValidationError,
    register_builtin_nodes,
)


def engine() -> WorkflowEngine:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    return WorkflowEngine(registry)


class WorkflowEngineTests(unittest.TestCase):
    def test_executes_typed_dag(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "hello",
                "nodes": [
                    {"id": "a", "type": "text.literal", "config": {"value": "K-Tools"}},
                    {"id": "b", "type": "text.literal", "config": {"value": "Neo"}},
                    {"id": "join", "type": "text.concat", "config": {"separator": " "}},
                ],
                "edges": [
                    {"sourceNode": "a", "sourcePort": "text", "targetNode": "join", "targetPort": "left"},
                    {"sourceNode": "b", "sourcePort": "text", "targetNode": "join", "targetPort": "right"},
                ],
            }
        )

        result = engine().execute(workflow)
        self.assertEqual(result.workflow_id, "hello")
        self.assertEqual(result.node_outputs["join"]["text"], "K-Tools Neo")
        self.assertTrue(result.run_id.startswith("run_"))

    def test_rejects_incompatible_port_types(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "bad-types",
                "nodes": [
                    {"id": "number", "type": "number.literal", "config": {"value": 7}},
                    {"id": "text", "type": "text.literal", "config": {"value": "x"}},
                    {"id": "join", "type": "text.concat"},
                ],
                "edges": [
                    {"sourceNode": "number", "sourcePort": "number", "targetNode": "join", "targetPort": "left"},
                    {"sourceNode": "text", "sourcePort": "text", "targetNode": "join", "targetPort": "right"},
                ],
            }
        )

        with self.assertRaisesRegex(WorkflowValidationError, "Incompatible edge"):
            engine().validate(workflow)

    def test_rejects_cycles(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "cycle",
                "nodes": [
                    {"id": "a", "type": "core.identity"},
                    {"id": "b", "type": "core.identity"},
                ],
                "edges": [
                    {"sourceNode": "a", "sourcePort": "value", "targetNode": "b", "targetPort": "value"},
                    {"sourceNode": "b", "sourcePort": "value", "targetNode": "a", "targetPort": "value"},
                ],
            }
        )

        with self.assertRaisesRegex(WorkflowValidationError, "cycle"):
            engine().validate(workflow)

    def test_rejects_missing_required_input(self) -> None:
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "missing",
                "nodes": [
                    {"id": "left", "type": "text.literal", "config": {"value": "x"}},
                    {"id": "join", "type": "text.concat"},
                ],
                "edges": [
                    {"sourceNode": "left", "sourcePort": "text", "targetNode": "join", "targetPort": "left"}
                ],
            }
        )

        with self.assertRaisesRegex(WorkflowValidationError, "join.right"):
            engine().validate(workflow)

    def test_optional_input_may_be_unconnected(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.optional",
                title="Optional",
                inputs={"value": PortDefinition(DataType.TEXT, required=False)},
                outputs={"text": PortDefinition(DataType.TEXT)},
            ),
            lambda inputs, _config, _context: {"text": inputs.get("value", "default")},
        )
        workflow = WorkflowDefinition.from_dict(
            {"id": "optional", "nodes": [{"id": "node", "type": "test.optional"}], "edges": []}
        )

        result = WorkflowEngine(registry).execute(workflow)
        self.assertEqual(result.node_outputs["node"]["text"], "default")

    def test_artifact_serialization_round_trip(self) -> None:
        artifact = Artifact.create(
            type=DataType.AUDIO,
            uri="file:///tmp/example.wav",
            produced_by="extract-audio",
            mime_type="audio/wav",
            metadata={"duration": 12.5},
        )

        rebuilt = Artifact.from_dict(artifact.to_dict())
        self.assertEqual(rebuilt, artifact)
        self.assertTrue(artifact.id.startswith("artifact_"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ktools_core import (
    Artifact,
    DataType,
    MemoryRunJournal,
    NodeDefinition,
    NodeRegistry,
    NodeRunStatus,
    PortDefinition,
    RunEvent,
    RunEventType,
    RunStatus,
    SQLiteRunJournal,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowExecutionError,
    register_builtin_nodes,
    to_json_safe,
)


def builtin_registry() -> NodeRegistry:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    return registry


def hello_workflow() -> WorkflowDefinition:
    return WorkflowDefinition.from_dict(
        {
            "id": "journal-hello",
            "nodes": [
                {"id": "a", "type": "text.literal", "config": {"value": "K-Tools"}},
                {"id": "b", "type": "text.literal", "config": {"value": "Neo"}},
                {"id": "join", "type": "text.concat", "config": {"separator": " "}},
            ],
            "edges": [
                {
                    "sourceNode": "a",
                    "sourcePort": "text",
                    "targetNode": "join",
                    "targetPort": "left",
                },
                {
                    "sourceNode": "b",
                    "sourcePort": "text",
                    "targetNode": "join",
                    "targetPort": "right",
                },
            ],
        }
    )


class MemoryJournalTests(unittest.TestCase):
    def test_success_event_order_and_outputs(self) -> None:
        journal = MemoryRunJournal()
        result = WorkflowEngine(builtin_registry(), journal=journal).execute(hello_workflow())

        event_types = [event.event_type for event in journal.events]
        self.assertEqual(
            event_types,
            [
                RunEventType.RUN_STARTED,
                RunEventType.NODE_STARTED,
                RunEventType.NODE_SUCCEEDED,
                RunEventType.NODE_STARTED,
                RunEventType.NODE_SUCCEEDED,
                RunEventType.NODE_STARTED,
                RunEventType.NODE_SUCCEEDED,
                RunEventType.RUN_SUCCEEDED,
            ],
        )
        self.assertTrue(all(event.run_id == result.run_id for event in journal.events))
        succeeded = [
            event for event in journal.events if event.event_type is RunEventType.NODE_SUCCEEDED
        ]
        self.assertEqual([event.node_id for event in succeeded], ["a", "b", "join"])
        self.assertEqual(succeeded[-1].payload["outputs"]["text"], "K-Tools Neo")

    def test_handler_failure_records_node_and_run_failure(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.fail",
                title="Fail",
                outputs={"text": PortDefinition(DataType.TEXT)},
            ),
            lambda _inputs, _config, _context: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        workflow = WorkflowDefinition.from_dict(
            {"id": "failure", "nodes": [{"id": "danger", "type": "test.fail"}], "edges": []}
        )
        journal = MemoryRunJournal()

        with self.assertRaisesRegex(WorkflowExecutionError, "Node danger failed: boom"):
            WorkflowEngine(registry, journal=journal).execute(workflow)

        self.assertEqual(
            [event.event_type for event in journal.events],
            [
                RunEventType.RUN_STARTED,
                RunEventType.NODE_STARTED,
                RunEventType.NODE_FAILED,
                RunEventType.RUN_FAILED,
            ],
        )
        self.assertEqual(journal.events[2].payload["errorType"], "WorkflowExecutionError")
        self.assertIn("Node danger failed: boom", journal.events[3].payload["errorMessage"])

    def test_output_contract_failure_is_journaled(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.bad-output",
                title="Bad output",
                outputs={"text": PortDefinition(DataType.TEXT)},
            ),
            lambda _inputs, _config, _context: {"unexpected": "x"},
        )
        workflow = WorkflowDefinition.from_dict(
            {
                "id": "bad-output",
                "nodes": [{"id": "broken", "type": "test.bad-output"}],
                "edges": [],
            }
        )
        journal = MemoryRunJournal()

        with self.assertRaisesRegex(WorkflowExecutionError, "unknown outputs"):
            WorkflowEngine(registry, journal=journal).execute(workflow)

        self.assertEqual(journal.events[-2].event_type, RunEventType.NODE_FAILED)
        self.assertEqual(journal.events[-1].event_type, RunEventType.RUN_FAILED)

    def test_default_engine_usage_remains_compatible(self) -> None:
        result = WorkflowEngine(builtin_registry()).execute(hello_workflow())
        self.assertEqual(result.node_outputs["join"]["text"], "K-Tools Neo")


class JsonSafeTests(unittest.TestCase):
    def test_normalizes_supported_runtime_values(self) -> None:
        artifact = Artifact.create(
            type=DataType.AUDIO,
            uri="file:///tmp/demo.wav",
            produced_by="node-1",
            metadata={"duration": 1.5},
        )
        normalized = to_json_safe(
            {
                "path": Path("some/file.txt"),
                "artifact": artifact,
                "enum": DataType.JSON,
                "items": {3, 1, 2},
                "notFinite": float("inf"),
            }
        )
        # The result must be accepted by strict JSON (no NaN/Infinity extension).
        encoded = json.dumps(normalized, allow_nan=False, sort_keys=True)
        self.assertIn('"type": "audio"', encoded)
        self.assertEqual(normalized["items"], [1, 2, 3])
        self.assertEqual(normalized["notFinite"]["value"], "Infinity")

    def test_unknown_object_does_not_persist_repr_contents(self) -> None:
        class SecretLike:
            def __repr__(self) -> str:
                return "TOKEN=do-not-persist-me"

        normalized = to_json_safe(SecretLike())
        encoded = json.dumps(normalized)
        self.assertTrue(normalized["__nonSerializable__"])
        self.assertNotIn("do-not-persist-me", encoded)
        self.assertIn("SecretLike", normalized["__type__"])


class SQLiteJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "runs.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_persists_success_and_reopens_for_queries(self) -> None:
        with SQLiteRunJournal(self.db_path) as journal:
            result = WorkflowEngine(builtin_registry(), journal=journal).execute(hello_workflow())
            run_id = result.run_id
            detail = journal.get_run_detail(run_id)
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.run.status, RunStatus.SUCCEEDED)
            self.assertEqual([node.status for node in detail.nodes], [
                NodeRunStatus.SUCCEEDED,
                NodeRunStatus.SUCCEEDED,
                NodeRunStatus.SUCCEEDED,
            ])
            join = next(node for node in detail.nodes if node.node_id == "join")
            self.assertEqual(join.outputs["text"], "K-Tools Neo")
            self.assertEqual(detail.events[0].event_type, RunEventType.RUN_STARTED)
            self.assertEqual(detail.events[-1].event_type, RunEventType.RUN_SUCCEEDED)

        with SQLiteRunJournal(self.db_path) as reopened:
            run = reopened.get_run(run_id)
            self.assertIsNotNone(run)
            assert run is not None
            self.assertEqual(run.status, RunStatus.SUCCEEDED)
            self.assertEqual(reopened.list_runs(1)[0].run_id, run_id)
            self.assertEqual(len(reopened.get_events(run_id)), 8)

    def test_persists_failure_details(self) -> None:
        registry = NodeRegistry()
        registry.register(
            NodeDefinition(
                type_id="test.fail",
                title="Fail",
                outputs={"text": PortDefinition(DataType.TEXT)},
            ),
            lambda _inputs, _config, _context: (_ for _ in ()).throw(ValueError("bad input")),
        )
        workflow = WorkflowDefinition.from_dict(
            {"id": "sqlite-failure", "nodes": [{"id": "bad", "type": "test.fail"}], "edges": []}
        )

        with SQLiteRunJournal(self.db_path) as journal:
            with self.assertRaisesRegex(WorkflowExecutionError, "Node bad failed: bad input"):
                WorkflowEngine(registry, journal=journal).execute(workflow)
            runs = journal.list_runs()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0].status, RunStatus.FAILED)
            self.assertIn("Node bad failed: bad input", runs[0].error_message or "")
            nodes = journal.get_node_runs(runs[0].run_id)
            self.assertEqual(nodes[0].status, NodeRunStatus.FAILED)

    def test_explicit_reconciliation_marks_incomplete_run_interrupted(self) -> None:
        run_id = "run_incomplete"
        workflow_id = "interrupted-workflow"
        with SQLiteRunJournal(self.db_path) as journal:
            journal.record(
                RunEvent.create(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    event_type=RunEventType.RUN_STARTED,
                )
            )
            journal.record(
                RunEvent.create(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    event_type=RunEventType.NODE_STARTED,
                    node_id="working",
                    node_type="test.work",
                )
            )

        with SQLiteRunJournal(self.db_path) as journal:
            reconciled = journal.reconcile_incomplete_runs("test process disappeared")
            self.assertEqual(reconciled, (run_id,))
            detail = journal.get_run_detail(run_id)
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.run.status, RunStatus.INTERRUPTED)
            self.assertEqual(detail.nodes[0].status, NodeRunStatus.INTERRUPTED)
            self.assertEqual(
                [event.event_type for event in detail.events[-2:]],
                [RunEventType.NODE_INTERRUPTED, RunEventType.RUN_INTERRUPTED],
            )
            self.assertEqual(journal.reconcile_incomplete_runs(), ())


if __name__ == "__main__":
    unittest.main()

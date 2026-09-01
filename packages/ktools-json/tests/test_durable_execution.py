from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ktools_core import (
    NodeRegistry,
    NodeRunStatus,
    RunEventType,
    RunStatus,
    SQLiteRunJournal,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowExecutionError,
    register_builtin_nodes,
)
from ktools_json import register_nodes


RECORDS = {
    "dataset": "durable-execution",
    "records": [
        {"id": 1, "label": "one"},
        {"id": 2, "label": "two"},
        {"id": 3, "label": "three"},
        {"id": 4, "label": "four"},
        {"id": 5, "label": "five"},
    ],
}


def registry_with_json() -> NodeRegistry:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    return registry


def workflow_for(output_dir: Path, *, mode: str = "parts") -> WorkflowDefinition:
    return WorkflowDefinition.from_dict(
        {
            "id": "durable-json-split",
            "nodes": [
                {
                    "id": "source",
                    "type": "json.literal",
                    "config": {"value": RECORDS},
                },
                {
                    "id": "splitter",
                    "type": "json.split",
                    "config": {
                        "mode": mode,
                        "parts": 2,
                        "output_dir": str(output_dir),
                        "prefix": "durable",
                    },
                },
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


class JsonDurableExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "runs.sqlite3"
        self.output_dir = self.root / "parts"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_real_json_workflow_is_queryable_after_success(self) -> None:
        with SQLiteRunJournal(self.db) as journal:
            result = WorkflowEngine(registry_with_json(), journal=journal).execute(
                workflow_for(self.output_dir)
            )
            run_id = result.run_id

            detail = journal.get_run_detail(run_id)
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.run.status, RunStatus.SUCCEEDED)
            self.assertEqual(detail.run.workflow_id, "durable-json-split")
            self.assertEqual(
                {node.node_id: node.status for node in detail.nodes},
                {
                    "source": NodeRunStatus.SUCCEEDED,
                    "splitter": NodeRunStatus.SUCCEEDED,
                },
            )

            splitter = next(node for node in detail.nodes if node.node_id == "splitter")
            self.assertEqual(splitter.outputs["summary"]["partCount"], 2)
            self.assertEqual(splitter.outputs["summary"]["itemCount"], 5)
            self.assertEqual(len(splitter.outputs["parts"]), 2)
            self.assertTrue(all(part["type"] == "json" for part in splitter.outputs["parts"]))
            self.assertEqual(detail.events[0].event_type, RunEventType.RUN_STARTED)
            self.assertEqual(detail.events[-1].event_type, RunEventType.RUN_SUCCEEDED)

        # Persistence must survive closing/reopening the journal connection.
        with SQLiteRunJournal(self.db) as reopened:
            detail = reopened.get_run_detail(run_id)
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.run.status, RunStatus.SUCCEEDED)
            self.assertEqual(len(detail.nodes), 2)

        written = sorted(self.output_dir.glob("*.json"))
        self.assertEqual(len(written), 2)
        reconstructed_items = []
        for path in written:
            part = json.loads(path.read_text(encoding="utf-8"))
            reconstructed_items.extend(part["records"])
        self.assertEqual(reconstructed_items, RECORDS["records"])

    def test_real_json_failure_is_durable_and_bound_to_splitter(self) -> None:
        with SQLiteRunJournal(self.db) as journal:
            with self.assertRaisesRegex(WorkflowExecutionError, "Node splitter failed: .*mode must be"):
                WorkflowEngine(registry_with_json(), journal=journal).execute(
                    workflow_for(self.output_dir, mode="not-a-mode")
                )

            runs = journal.list_runs()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0].status, RunStatus.FAILED)
            nodes = {node.node_id: node for node in journal.get_node_runs(runs[0].run_id)}
            self.assertEqual(nodes["source"].status, NodeRunStatus.SUCCEEDED)
            self.assertEqual(nodes["splitter"].status, NodeRunStatus.FAILED)
            self.assertIn("mode must be", nodes["splitter"].error_message or "")
            self.assertFalse(self.output_dir.exists())
            self.assertEqual(
                [event.event_type for event in journal.get_events(runs[0].run_id)][-2:],
                [RunEventType.NODE_FAILED, RunEventType.RUN_FAILED],
            )


if __name__ == "__main__":
    unittest.main()

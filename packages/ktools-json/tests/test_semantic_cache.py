from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ktools_core import NodeRunStatus, SQLiteNodeCache, SQLiteRunJournal, WorkflowDefinition, WorkflowEdge, WorkflowEngine, WorkflowNode
from ktools_core.builtin import register_builtin_nodes
from ktools_core.registry import NodeRegistry

from ktools_json import capability
from ktools_json.node import register_nodes


class JsonSemanticCacheIntegrationTests(unittest.TestCase):
    def test_real_split_plan_is_reused_after_cache_close_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache_path = root / "cache.sqlite3"
            journal_path = root / "runs.sqlite3"
            records = {
                "dataset": "m4-real-cache",
                "records": [
                    {"id": index, "label": f"record-{index}", "payload": "x" * 40}
                    for index in range(2000)
                ],
            }
            workflow = WorkflowDefinition(
                id="json-real-pure-cache",
                nodes=(
                    WorkflowNode(id="source", type="json.literal", config={"value": records}),
                    WorkflowNode(id="planner", type="json.split.plan", config={"mode": "parts", "parts": 8}),
                ),
                edges=(
                    WorkflowEdge(
                        source_node="source",
                        source_port="json",
                        target_node="planner",
                        target_port="json_data",
                    ),
                ),
            )
            registry = NodeRegistry()
            register_builtin_nodes(registry)
            register_nodes(registry)

            with patch(
                "ktools_json.node.split_json_document",
                wraps=capability.split_json_document,
            ) as split_owner:
                with SQLiteRunJournal(journal_path) as journal:
                    with SQLiteNodeCache(cache_path) as cache:
                        first = WorkflowEngine(registry, journal=journal, cache=cache).execute(workflow)
                    # Reopen the cache to prove the second run does not depend on
                    # process-memory state from the first execution.
                    with SQLiteNodeCache(cache_path) as cache:
                        second = WorkflowEngine(registry, journal=journal, cache=cache).execute(workflow)
                    second_detail = journal.get_run_detail(second.run_id)

                self.assertEqual(split_owner.call_count, 1)

            self.assertEqual(first.node_outputs["planner"], second.node_outputs["planner"])
            plan = second.node_outputs["planner"]["plan"]
            self.assertEqual(plan["itemCount"], 2000)
            self.assertEqual(plan["partCount"], 8)
            self.assertIsNotNone(second_detail)
            assert second_detail is not None
            statuses = {node.node_id: node.status for node in second_detail.nodes}
            self.assertIs(statuses["source"], NodeRunStatus.CACHED)
            self.assertIs(statuses["planner"], NodeRunStatus.CACHED)


if __name__ == "__main__":
    unittest.main()

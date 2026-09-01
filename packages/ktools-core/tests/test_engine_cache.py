from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.cache_store import CacheError, SQLiteNodeCache
from ktools_core.diagnostics import DiagnosticsSession
from ktools_core.engine import WorkflowEngine
from ktools_core.journal import MemoryRunJournal, NodeRunStatus, RunEventType
from ktools_core.models import (
    Artifact,
    CachePolicy,
    DataType,
    NodeDefinition,
    PortDefinition,
    WorkflowDefinition,
    WorkflowNode,
)
from ktools_core.registry import NodeExecutionContext, NodeRegistry
from ktools_core.sqlite_journal import SQLiteRunJournal


class EngineSemanticCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _workflow(self, node_type: str, *, config: dict | None = None) -> WorkflowDefinition:
        return WorkflowDefinition(
            id="cache-test",
            nodes=(WorkflowNode(id="work", type=node_type, config=dict(config or {})),),
            edges=(),
        )

    def test_second_equivalent_run_reuses_cache_without_calling_handler(self) -> None:
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, config: dict, _context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            return {"text": config["value"]}

        registry.register(
            NodeDefinition(
                type_id="test.pure",
                title="Pure",
                outputs={"text": PortDefinition(DataType.TEXT)},
                version="1",
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        cache = SQLiteNodeCache(self.root / "cache.sqlite3")
        first_journal = MemoryRunJournal()
        second_journal = MemoryRunJournal()
        diagnostics = DiagnosticsSession(self.root / "diagnostics", session_id="cache-diag")
        try:
            first = WorkflowEngine(registry, journal=first_journal, cache=cache).execute(
                self._workflow("test.pure", config={"value": "Neo"})
            )
            second = WorkflowEngine(
                registry,
                journal=second_journal,
                cache=cache,
                diagnostics=diagnostics,
            ).execute(self._workflow("test.pure", config={"value": "Neo"}))
        finally:
            diagnostics.finalize(status="SUCCEEDED")
            cache.close()

        self.assertEqual(calls["count"], 1)
        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(second.node_outputs["work"]["text"], "Neo")
        self.assertEqual(
            [event.event_type for event in second_journal.events],
            [RunEventType.RUN_STARTED, RunEventType.NODE_CACHED, RunEventType.RUN_SUCCEEDED],
        )
        cached_event = second_journal.events[1]
        self.assertEqual(cached_event.payload["originRunId"], first.run_id)
        self.assertEqual(cached_event.payload["originNodeId"], "work")
        decisions = [
            event
            for event in diagnostics.events
            if event.category == "workflow.cache" and event.kind.value == "DECISION"
        ]
        self.assertTrue(
            any(event.context.get("reason") == "validated-cache-hit" for event in decisions)
        )

    def test_sqlite_journal_projects_cached_node_without_node_started(self) -> None:
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, _config: dict, _context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            return {"text": "cached"}

        registry.register(
            NodeDefinition(
                type_id="test.sqlite-cache",
                title="SQLite cache",
                outputs={"text": PortDefinition(DataType.TEXT)},
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        cache = SQLiteNodeCache(self.root / "cache.sqlite3")
        journal = SQLiteRunJournal(self.root / "runs.sqlite3")
        try:
            WorkflowEngine(registry, journal=journal, cache=cache).execute(
                self._workflow("test.sqlite-cache")
            )
            second = WorkflowEngine(registry, journal=journal, cache=cache).execute(
                self._workflow("test.sqlite-cache")
            )
            detail = journal.get_run_detail(second.run_id)
        finally:
            journal.close()
            cache.close()

        self.assertEqual(calls["count"], 1)
        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(len(detail.nodes), 1)
        self.assertIs(detail.nodes[0].status, NodeRunStatus.CACHED)
        self.assertEqual(
            [event.event_type for event in detail.events],
            [RunEventType.RUN_STARTED, RunEventType.NODE_CACHED, RunEventType.RUN_SUCCEEDED],
        )

    def test_config_change_misses_cache_and_executes_again(self) -> None:
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, config: dict, _context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            return {"text": config["value"]}

        registry.register(
            NodeDefinition(
                type_id="test.config",
                title="Config",
                outputs={"text": PortDefinition(DataType.TEXT)},
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        with SQLiteNodeCache(self.root / "cache.sqlite3") as cache:
            WorkflowEngine(registry, cache=cache).execute(
                self._workflow("test.config", config={"value": "A"})
            )
            WorkflowEngine(registry, cache=cache).execute(
                self._workflow("test.config", config={"value": "B"})
            )
        self.assertEqual(calls["count"], 2)

    def test_never_policy_always_executes(self) -> None:
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, _config: dict, _context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            return {"text": str(calls["count"])}

        registry.register(
            NodeDefinition(
                type_id="test.side-effect",
                title="Never cached",
                outputs={"text": PortDefinition(DataType.TEXT)},
                cache_policy=CachePolicy.NEVER,
            ),
            handler,
        )
        with SQLiteNodeCache(self.root / "cache.sqlite3") as cache:
            first = WorkflowEngine(registry, cache=cache).execute(self._workflow("test.side-effect"))
            second = WorkflowEngine(registry, cache=cache).execute(self._workflow("test.side-effect"))
        self.assertEqual(calls["count"], 2)
        self.assertEqual(first.node_outputs["work"]["text"], "1")
        self.assertEqual(second.node_outputs["work"]["text"], "2")

    def test_missing_cached_output_artifact_forces_execution(self) -> None:
        calls = {"count": 0}
        output = self.root / "fixture-output.bin"
        registry = NodeRegistry()

        def handler(_inputs: dict, config: dict, context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            path = Path(config["path"])
            path.write_bytes(b"deterministic-fixture")
            return {
                "file": Artifact.create(
                    type=DataType.FILE,
                    uri=path.resolve().as_uri(),
                    produced_by=f"{context.run_id}/{context.node_id}",
                )
            }

        registry.register(
            NodeDefinition(
                type_id="test.file-fixture",
                title="File fixture",
                outputs={"file": PortDefinition(DataType.FILE)},
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        workflow = self._workflow("test.file-fixture", config={"path": str(output)})
        diagnostics = DiagnosticsSession(self.root / "diagnostics", session_id="invalid-diag")
        with SQLiteNodeCache(self.root / "cache.sqlite3") as cache:
            WorkflowEngine(registry, cache=cache).execute(workflow)
            self.assertEqual(calls["count"], 1)
            output.unlink()
            second = WorkflowEngine(
                registry, cache=cache, diagnostics=diagnostics
            ).execute(workflow)
        diagnostics.finalize(status="SUCCEEDED")

        self.assertEqual(calls["count"], 2)
        self.assertTrue(output.exists())
        self.assertIsInstance(second.node_outputs["work"]["file"], Artifact)
        invalidation = [
            event
            for event in diagnostics.events
            if event.category == "workflow.cache" and event.context.get("reason") == "missing"
        ]
        self.assertTrue(invalidation)

    def test_cache_read_and_write_failures_do_not_break_workflow_execution(self) -> None:
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, _config: dict, _context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            return {"text": "still-runs"}

        registry.register(
            NodeDefinition(
                type_id="test.fail-open",
                title="Fail open",
                outputs={"text": PortDefinition(DataType.TEXT)},
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )

        class BrokenCache:
            def get(self, signature: str):
                raise CacheError(f"read unavailable for {signature}")

            def put(self, **_kwargs):
                raise CacheError("write unavailable")

            def mark_used(self, signature: str) -> None:
                raise CacheError(f"touch unavailable for {signature}")

            def invalidate(self, signature: str) -> None:
                raise CacheError(f"invalidate unavailable for {signature}")

        diagnostics = DiagnosticsSession(self.root / "diagnostics", session_id="fail-open-diag")
        result = WorkflowEngine(
            registry,
            cache=BrokenCache(),
            diagnostics=diagnostics,
        ).execute(self._workflow("test.fail-open"))
        diagnostics.finalize(status="SUCCEEDED")

        self.assertEqual(calls["count"], 1)
        self.assertEqual(result.node_outputs["work"]["text"], "still-runs")
        reasons = {
            event.context.get("reason")
            for event in diagnostics.events
            if event.category == "workflow.cache"
        }
        self.assertIn("cache-read-error", reasons)
        self.assertIn("cache-write-unsupported-or-failed", reasons)

    def test_uncacheable_output_does_not_turn_successful_node_into_failure(self) -> None:
        registry = NodeRegistry()

        def handler(_inputs: dict, _config: dict, _context: NodeExecutionContext) -> dict:
            return {"value": self.root / "raw-path.txt"}

        registry.register(
            NodeDefinition(
                type_id="test.path-output",
                title="Path output",
                outputs={"value": PortDefinition(DataType.ANY)},
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        diagnostics = DiagnosticsSession(self.root / "diagnostics", session_id="path-diag")
        with SQLiteNodeCache(self.root / "cache.sqlite3") as cache:
            result = WorkflowEngine(
                registry,
                cache=cache,
                diagnostics=diagnostics,
            ).execute(self._workflow("test.path-output"))
        diagnostics.finalize(status="SUCCEEDED")

        self.assertEqual(result.node_outputs["work"]["value"], self.root / "raw-path.txt")
        self.assertTrue(
            any(
                event.context.get("reason") == "cache-write-unsupported-or-failed"
                for event in diagnostics.events
                if event.category == "workflow.cache"
            )
        )


if __name__ == "__main__":
    unittest.main()

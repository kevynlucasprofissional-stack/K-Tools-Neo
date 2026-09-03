from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ktools_core.engine import WorkflowEngine
from ktools_core.models import Artifact, DataType, WorkflowDefinition, WorkflowNode, WorkflowEdge
from ktools_core.registry import NodeRegistry
from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.sqlite_journal import SQLiteRunJournal
from ktools_core.builtin import register_builtin_nodes
from ktools_filesystem.node import register_nodes


class FolderScanEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        
        self.db_path = self.root / "cache.sqlite"
        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)
        
        self.run_journal = SQLiteRunJournal(str(self.db_path))
        self.artifact_registry = SQLiteArtifactRegistry(str(self.db_path))
        
        self.engine = WorkflowEngine(
            registry=self.registry,
            journal=self.run_journal,
            artifact_registry=self.artifact_registry
        )

    def tearDown(self) -> None:
        self.artifact_registry.close()
        self.run_journal.close()
        self.temp.cleanup()

    def test_workflow_execution_and_never_cache(self) -> None:
        # Create some files
        scan_dir = self.root / "scan"
        scan_dir.mkdir()
        (scan_dir / "a.txt").write_text("a")
        
        workflow = WorkflowDefinition(
            id="test-workflow",
            nodes=(
                WorkflowNode(id="n1", type="folder.literal", config={"path": str(scan_dir)}),
                WorkflowNode(id="n2", type="folder.scan_files", config={}),
            ),
            edges=(
                WorkflowEdge(
                    source_node="n1",
                    source_port="folder",
                    target_node="n2",
                    target_port="folder",
                ),
            ),
        )
        
        result1 = self.engine.execute(workflow)
        self.assertIn("n2", result1.node_outputs)
        files1 = result1.node_outputs["n2"]["files"]
        self.assertEqual(len(files1), 1)
        
        # Verify artifact is snapshotted
        records = self.artifact_registry.list_for_artifact(files1[0].id)
        self.assertGreater(len(records), 0)
        self.assertIsNotNone(records[0].snapshot)
        
        # Add a file, run again
        (scan_dir / "b.txt").write_text("b")
        result2 = self.engine.execute(workflow)
        self.assertIn("n2", result2.node_outputs)
        
        # Verify it wasn't cached and we get 2 files
        events = self.run_journal.get_events(result2.run_id)
        n2_events = [e for e in events if e.node_id == "n2" and e.event_type == "NODE_CACHED"]
        self.assertEqual(len(n2_events), 0, "folder.scan_files MUST NOT be cached")
        
        files2 = result2.node_outputs["n2"]["files"]
        self.assertEqual(len(files2), 2)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ktools_core.engine import WorkflowEngine
from ktools_core.models import (
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    DataType,
)
from ktools_core.registry import NodeRegistry
from ktools_core.diagnostics import DiagnosticsSession
from ktools_core.builtin import register_builtin_nodes
from ktools_filesystem.node import register_nodes


class FilesystemDriveScannerEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        # Setup test files
        self.d = self.root / "drive_root"
        self.d.mkdir()
        (self.d / "doc.pdf").write_bytes(b"sample pdf")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workflow_execution(self):
        workflow = WorkflowDefinition(
            id="w_drive_scan",
            nodes=[
                WorkflowNode(
                    id="n_folder",
                    type="folder.literal",
                    config={"path": str(self.d)},
                ),
                WorkflowNode(
                    id="n_scan",
                    type="filesystem.drive_stream_scan",
                    config={"base_name": "gdrive_scan", "verify_stability": False},
                ),
            ],
            edges=[
                WorkflowEdge("n_folder", "folder", "n_scan", "folder"),
            ],
        )

        result = self.engine.execute(workflow)
        out_db = result.node_outputs["n_scan"]["database"]
        out_csv = result.node_outputs["n_scan"]["csv"]
        out_report = result.node_outputs["n_scan"]["report"]

        self.assertEqual(out_db.type, DataType.FILE)
        self.assertEqual(out_csv.type, DataType.FILE)
        self.assertEqual(out_report.type, DataType.JSON)
        self.assertEqual(out_report.metadata["total_files"], 1)


if __name__ == "__main__":
    unittest.main()

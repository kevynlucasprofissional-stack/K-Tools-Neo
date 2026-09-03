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


class FilesystemReportEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        # Setup test files
        self.d = self.root / "sample_folder"
        self.d.mkdir()
        (self.d / "file1.txt").write_text("content 1", encoding="utf-8")
        (self.d / "file2.json").write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workflow_execution(self):
        workflow = WorkflowDefinition(
            id="w_report",
            nodes=[
                WorkflowNode(
                    id="n_folder",
                    type="folder.literal",
                    config={"path": str(self.d)},
                ),
                WorkflowNode(
                    id="n_report",
                    type="filesystem.structure_report",
                    config={"base_name": "sample_inventory"},
                ),
            ],
            edges=[
                WorkflowEdge("n_folder", "folder", "n_report", "folder"),
            ],
        )

        result = self.engine.execute(workflow)
        out_csv = result.node_outputs["n_report"]["csv"]
        out_txt = result.node_outputs["n_report"]["txt"]
        out_json = result.node_outputs["n_report"]["json"]

        self.assertEqual(out_csv.type, DataType.FILE)
        self.assertEqual(out_txt.type, DataType.FILE)
        self.assertEqual(out_json.type, DataType.JSON)
        self.assertEqual(out_json.metadata["total_files"], 2)


if __name__ == "__main__":
    unittest.main()

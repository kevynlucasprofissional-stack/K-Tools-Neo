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
from ktools_text.node import register_nodes

SAMPLE_TLDV_HTML = """
<!DOCTYPE html>
<html>
<body>
<div id="transcript-container">
    <p data-index="0">
        <div class="inline">Alice</div>
        <span data-speaker="false" data-time="1000">Welcome</span>
        <span data-speaker="false" data-time="2000">team.</span>
    </p>
</div>
</body>
</html>
"""


class TextTldvEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        self.html_file = self.root / "recording.html"
        self.html_file.write_text(SAMPLE_TLDV_HTML, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workflow_execution(self):
        workflow = WorkflowDefinition(
            id="w_tldv",
            nodes=[
                WorkflowNode(
                    id="n_html",
                    type="file.literal",
                    config={"path": str(self.html_file)},
                ),
                WorkflowNode(
                    id="n_extract",
                    type="text.tldv_extract",
                    config={"title": "Sprint Planning"},
                ),
            ],
            edges=[
                WorkflowEdge("n_html", "file", "n_extract", "html"),
            ],
        )

        result = self.engine.execute(workflow)
        out_md = result.node_outputs["n_extract"]["markdown"]
        out_srt = result.node_outputs["n_extract"]["srt"]
        out_json = result.node_outputs["n_extract"]["json"]

        self.assertEqual(out_md.type, DataType.FILE)
        self.assertEqual(out_srt.type, DataType.FILE)
        self.assertEqual(out_json.type, DataType.JSON)
        self.assertEqual(out_json.metadata["title"], "Sprint Planning")
        self.assertEqual(out_json.metadata["total_blocks"], 1)


if __name__ == "__main__":
    unittest.main()

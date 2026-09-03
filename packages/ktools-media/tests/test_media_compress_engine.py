import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_core.engine import WorkflowEngine
from ktools_core.models import (
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    DataType,
)
from ktools_core.registry import NodeRegistry
from ktools_core.diagnostics import DiagnosticsSession
from ktools_media.node import register_nodes
from ktools_core.builtin import register_builtin_nodes

class MediaCompressEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)
        
        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("ktools_core.diagnostics.subprocess.run")
    def test_workflow_execution_and_diagnostics(self, mock_subprocess_run):
        def fake_run(*args, **kwargs):
            cmd = args[0]
            tmp_out = Path(cmd[-1])
            if str(tmp_out).endswith(".tmp"):
                tmp_out.write_bytes(b"compressed")
                
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "fake stdout"
            mock_res.stderr = "fake stderr"
            return mock_res
            
        mock_subprocess_run.side_effect = fake_run

        in_video = self.root / "test.mp4"
        in_video.write_bytes(b"fake mp4")
        
        workflow = WorkflowDefinition(
            id="w_compress",
            nodes=[
                WorkflowNode(
                    id="n_in",
                    type="file.literal",
                    config={"path": str(in_video)},
                ),
                WorkflowNode(
                    id="n_comp",
                    type="media.compress_video",
                    config={"crf": 25, "preset": "ultrafast"},
                )
            ],
            edges=[
                WorkflowEdge("n_in", "file", "n_comp", "video")
            ]
        )
        
        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs["n_comp"]["video"]
        self.assertEqual(out_artifact.type, DataType.VIDEO)
        
        events = self.diagnostics.events
        subproc_events = [e for e in events if e.kind == "SUBPROCESS"]
        
        # 1 call = 2 events
        self.assertGreater(len(subproc_events), 0)

if __name__ == '__main__':
    unittest.main()

import subprocess
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
    Artifact,
)
from ktools_core.registry import NodeRegistry
from ktools_core.diagnostics import DiagnosticsSession
from ktools_media.node import register_nodes
from ktools_core.builtin import register_builtin_nodes


class MediaConvertEngineTests(unittest.TestCase):
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
            # Create a mock CompletedProcess
            # We must also simulate touching the output file so atomic os.replace works
            cmd = args[0]
            tmp_out = Path(cmd[-1])
            if str(tmp_out).endswith(".tmp"):
                tmp_out.write_bytes(b"converted_data")
            
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "fake stdout"
            mock_res.stderr = "fake stderr"
            return mock_res
            
        mock_subprocess_run.side_effect = fake_run

        in_audio = self.root / "test.wav"
        in_audio.write_bytes(b"fake wav")
        
        workflow = WorkflowDefinition(
            id="w_convert",
            nodes=[
                WorkflowNode(
                    id="n_in",
                    type="file.literal",
                    config={"path": str(in_audio)},
                ),
                WorkflowNode(
                    id="n_conv",
                    type="media.convert_audio",
                    config={"format": "mp3", "bitrate": "128k"},
                )
            ],
            edges=[
                WorkflowEdge("n_in", "file", "n_conv", "audio")
            ]
        )
        
        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs["n_conv"]["audio"]
        self.assertEqual(out_artifact.type, DataType.AUDIO)
        
        events = self.diagnostics.events
        subproc_events = [e for e in events if e.kind == "SUBPROCESS"]
        self.assertGreater(len(subproc_events), 0)
        
        cmds = [e.context.get("command", []) for e in subproc_events]
        has_ffmpeg = any("ffmpeg" in c[0] for c in cmds if c)
        self.assertTrue(has_ffmpeg, "Did not record ffmpeg execution")


if __name__ == '__main__':
    unittest.main()

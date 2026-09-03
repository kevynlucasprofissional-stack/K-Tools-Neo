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
from ktools_filesystem.node import register_nodes as register_fs_nodes


class MediaSubfolderAudioEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_fs_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        # Setup folders
        self.mod1 = self.root / "M01"
        self.mod1.mkdir(parents=True)
        (self.mod1 / "v1.mp4").write_bytes(b"vid1")
        (self.mod1 / "v2.mp4").write_bytes(b"vid2")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("ktools_core.diagnostics.subprocess.run")
    def test_workflow_execution_and_diagnostics(self, mock_subprocess_run):
        def fake_run(*args, **kwargs):
            cmd = args[0]
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"subfolder_audio_data")
            elif str(out_file).endswith(".wav"):
                out_file.write_bytes(b"wav_temp")

            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "ffmpeg stdout"
            mock_res.stderr = ""
            return mock_res

        mock_subprocess_run.side_effect = fake_run

        workflow = WorkflowDefinition(
            id="w_subfolder_audio",
            nodes=[
                WorkflowNode(
                    id="n_folder",
                    type="folder.literal",
                    config={"path": str(self.root)},
                ),
                WorkflowNode(
                    id="n_batch",
                    type="media.extract_and_join_by_subfolder",
                    config={"format": "m4a"},
                ),
            ],
            edges=[
                WorkflowEdge("n_folder", "folder", "n_batch", "folder"),
            ],
        )

        result = self.engine.execute(workflow)
        out_audios = result.node_outputs["n_batch"]["audios"]
        out_report = result.node_outputs["n_batch"]["report"]

        self.assertIsInstance(out_audios, list)
        self.assertGreater(len(out_audios), 0)
        self.assertEqual(out_report.type, DataType.JSON)

        subproc_events = [e for e in self.diagnostics.events if e.kind == "SUBPROCESS"]
        self.assertGreater(len(subproc_events), 0)


if __name__ == "__main__":
    unittest.main()

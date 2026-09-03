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


class MediaAlacEngineTests(unittest.TestCase):
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
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"alac_m4a_encoded")
            elif "-f" in cmd and "s16le" in cmd:
                out_file.write_bytes(b"pcm_stream_exact_match")

            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "ffmpeg output"
            mock_res.stderr = ""
            return mock_res

        mock_subprocess_run.side_effect = fake_run

        in_wav = self.root / "track.wav"
        in_wav.write_bytes(b"wav_input_data")

        workflow = WorkflowDefinition(
            id="w_alac",
            nodes=[
                WorkflowNode(
                    id="n_lit",
                    type="file.literal",
                    config={"path": str(in_wav)},
                ),
                WorkflowNode(
                    id="n_alac",
                    type="media.convert_lossless_alac",
                    config={"verify_bit_exact": True},
                ),
            ],
            edges=[
                WorkflowEdge("n_lit", "file", "n_alac", "audio"),
            ],
        )

        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs["n_alac"]["audio"]

        self.assertEqual(out_artifact.type, DataType.AUDIO)
        self.assertEqual(out_artifact.metadata.get("codec"), "alac")
        self.assertTrue(out_artifact.metadata.get("verified_bit_exact"))

        subproc_events = [e for e in self.diagnostics.events if e.kind == "SUBPROCESS"]
        self.assertGreater(len(subproc_events), 0)


if __name__ == "__main__":
    unittest.main()

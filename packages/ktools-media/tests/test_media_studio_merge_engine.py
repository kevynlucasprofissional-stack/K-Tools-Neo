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
    NodeDefinition,
    PortDefinition,
    CachePolicy,
)
from ktools_core.registry import NodeRegistry
from ktools_core.diagnostics import DiagnosticsSession
from ktools_media.node import register_nodes
from ktools_core.builtin import register_builtin_nodes


class MediaStudioMergeEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        # Mock multi audio/video generator
        def _mock_multi_src(inputs, config, context):
            f1 = self.root / "track10.mp4"
            f2 = self.root / "track2.mp3"
            f1.write_bytes(b"vid_data")
            f2.write_bytes(b"aud_data")
            return {
                "sources": [
                    Artifact.create(type=DataType.VIDEO, uri=f1.as_uri()),
                    Artifact.create(type=DataType.AUDIO, uri=f2.as_uri()),
                ]
            }

        self.registry.register(
            NodeDefinition(
                type_id="test.multi_source",
                title="Mock Multi Source",
                category="Test",
                inputs={},
                outputs={"sources": PortDefinition(DataType.FILE_SET)},
                version="1",
                cache_policy=CachePolicy.NEVER,
            ),
            _mock_multi_src,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("ktools_core.diagnostics.subprocess.run")
    def test_workflow_execution_and_diagnostics(self, mock_subprocess_run):
        def fake_run(*args, **kwargs):
            cmd = args[0]
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"studio_final_merged_content")
            elif str(out_file).endswith(".wav"):
                out_file.write_bytes(b"wav_extracted")

            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "ffmpeg stdout"
            mock_res.stderr = ""
            return mock_res

        mock_subprocess_run.side_effect = fake_run

        workflow = WorkflowDefinition(
            id="w_studio_merge",
            nodes=[
                WorkflowNode(
                    id="n_src",
                    type="test.multi_source",
                    config={},
                ),
                WorkflowNode(
                    id="n_merge",
                    type="media.merge_audio_studio",
                    config={"natural_sort": True, "format": "m4a"},
                ),
            ],
            edges=[
                WorkflowEdge("n_src", "sources", "n_merge", "sources"),
            ],
        )

        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs["n_merge"]["audio"]

        self.assertEqual(out_artifact.type, DataType.AUDIO)
        self.assertIn("sha256", out_artifact.metadata)
        self.assertEqual(out_artifact.metadata["item_count"], 2)

        subproc_events = [e for e in self.diagnostics.events if e.kind == "SUBPROCESS"]
        self.assertGreater(len(subproc_events), 0)


if __name__ == "__main__":
    unittest.main()

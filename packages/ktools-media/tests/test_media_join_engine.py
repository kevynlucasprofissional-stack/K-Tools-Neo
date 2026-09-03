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
    Artifact,
)
from ktools_core.registry import NodeRegistry
from ktools_core.diagnostics import DiagnosticsSession
from ktools_media.node import register_nodes
from ktools_core.builtin import register_builtin_nodes

class MediaJoinEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)
        
        self.diagnostics = DiagnosticsSession(self.root / "logs")
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)
        
        # We need a custom node that produces a FILE_SET of artifacts
        # Wait, we can just inject a mock node or use multiple file literals?
        # A mock node is easier.
        def _mock_multi_audio(inputs, config, context):
            a1 = self.root / "a.mp3"
            a2 = self.root / "b.mp3"
            a1.write_bytes(b"A")
            a2.write_bytes(b"B")
            return {
                "set": [
                    Artifact.create(type=DataType.AUDIO, uri=a1.as_uri()),
                    Artifact.create(type=DataType.AUDIO, uri=a2.as_uri()),
                ]
            }
        
        from ktools_core.models import NodeDefinition, PortDefinition, CachePolicy
        self.registry.register(
            NodeDefinition(
                type_id="test.multi_audio",
                title="Mock",
                category="Test",
                inputs={},
                outputs={"set": PortDefinition(DataType.FILE_SET)},
                version="1",
                cache_policy=CachePolicy.NEVER,
            ),
            _mock_multi_audio
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("ktools_core.diagnostics.subprocess.run")
    def test_workflow_execution_and_diagnostics(self, mock_subprocess_run):
        def fake_run(*args, **kwargs):
            cmd = args[0]
            tmp_out = Path(cmd[-1])
            if str(tmp_out).endswith(".tmp"):
                tmp_out.write_bytes(b"joined")
            elif str(tmp_out).endswith(".wav"):
                tmp_out.write_bytes(b"wav")
                
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "fake stdout"
            mock_res.stderr = "fake stderr"
            return mock_res
            
        mock_subprocess_run.side_effect = fake_run

        workflow = WorkflowDefinition(
            id="w_join",
            nodes=[
                WorkflowNode(
                    id="n_multi",
                    type="test.multi_audio",
                    config={},
                ),
                WorkflowNode(
                    id="n_join",
                    type="media.join_audios",
                    config={"format": "wav"},
                )
            ],
            edges=[
                WorkflowEdge("n_multi", "set", "n_join", "audios")
            ]
        )
        
        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs["n_join"]["audio"]
        self.assertEqual(out_artifact.type, DataType.AUDIO)
        
        events = self.diagnostics.events
        subproc_events = [e for e in events if e.kind == "SUBPROCESS"]
        
        # 3 calls * 2 events per call (start/finish) = 6 events
        self.assertEqual(len(subproc_events), 6)

if __name__ == '__main__':
    unittest.main()

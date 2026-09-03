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


class MediaJoinVideosEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)

        self.diagnostics = DiagnosticsSession(self.root / 'logs')
        self.engine = WorkflowEngine(self.registry, diagnostics=self.diagnostics)

        # Mock multi video generator node
        def _mock_multi_video(inputs, config, context):
            v1 = self.root / 'v1.mp4'
            v2 = self.root / 'v2.mp4'
            v1.write_bytes(b'video1')
            v2.write_bytes(b'video2')
            return {
                'videos': [
                    Artifact.create(type=DataType.VIDEO, uri=v1.as_uri()),
                    Artifact.create(type=DataType.VIDEO, uri=v2.as_uri()),
                ]
            }

        self.registry.register(
            NodeDefinition(
                type_id='test.multi_video',
                title='Mock Multi Video',
                category='Test',
                inputs={},
                outputs={'videos': PortDefinition(DataType.FILE_SET)},
                version='1',
                cache_policy=CachePolicy.NEVER,
            ),
            _mock_multi_video,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch('ktools_core.diagnostics.subprocess.run')
    def test_workflow_execution_and_diagnostics(self, mock_subprocess_run):
        def fake_run(*args, **kwargs):
            cmd = args[0]
            tmp_out = Path(cmd[-1])
            if str(tmp_out).endswith('.tmp'):
                tmp_out.write_bytes(b'joined_video_data')
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = 'ffmpeg stdout'
            mock_res.stderr = ''
            return mock_res

        mock_subprocess_run.side_effect = fake_run

        workflow = WorkflowDefinition(
            id='w_join_videos',
            nodes=[
                WorkflowNode(
                    id='n_src',
                    type='test.multi_video',
                    config={},
                ),
                WorkflowNode(
                    id='n_join',
                    type='media.join_videos',
                    config={'fast_copy': True},
                ),
            ],
            edges=[
                WorkflowEdge('n_src', 'videos', 'n_join', 'videos'),
            ],
        )

        result = self.engine.execute(workflow)
        out_artifact = result.node_outputs['n_join']['video']
        self.assertEqual(out_artifact.type, DataType.VIDEO)

        subproc_events = [e for e in self.diagnostics.events if e.kind == 'SUBPROCESS']
        self.assertGreater(len(subproc_events), 0)


if __name__ == '__main__':
    unittest.main()

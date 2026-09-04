import unittest
from unittest.mock import MagicMock, patch

from ktools_core.engine import WorkflowEngine
from ktools_core.models import (
    DataType,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)
from ktools_core.registry import NodeRegistry

from ktools_youtube.engine.service import YouTubeDownloadResult
from ktools_youtube.node import register_nodes


class TestYouTubeNode(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()
        register_nodes(self.registry)

    def test_node_definition_contracts(self):
        node_def = self.registry.definition("youtube.download")
        self.assertEqual(node_def.type_id, "youtube.download")
        self.assertEqual(node_def.category, "Download")

        # Ports
        self.assertIn("url", node_def.inputs)
        self.assertEqual(node_def.inputs["url"].type, DataType.TEXT)
        self.assertIn("files", node_def.outputs)
        self.assertEqual(node_def.outputs["files"].type, DataType.FILE_SET)
        self.assertIn("folder", node_def.outputs)
        self.assertEqual(node_def.outputs["folder"].type, DataType.FOLDER)
        self.assertIn("metadata", node_def.outputs)
        self.assertEqual(node_def.outputs["metadata"].type, DataType.JSON)

    @patch("ktools_youtube.node.YouTubeDownloadService")
    def test_workflow_engine_execution(self, mock_service_cls):
        mock_instance = MagicMock()
        mock_service_cls.return_value = mock_instance
        mock_instance.download.return_value = YouTubeDownloadResult(
            files=["/tmp/video_001.mp4", "/tmp/video_002.mp4"],
            folder="/tmp",
            metadata={"title": "Test YouTube Video", "duration": 120},
            auth_used=False,
        )

        workflow = WorkflowDefinition(
            id="wf-yt-download",
            nodes=(
                WorkflowNode(
                    id="download-step",
                    type="youtube.download",
                    config={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                ),
            ),
            edges=(),
        )

        engine = WorkflowEngine(self.registry)
        result = engine.execute(workflow)

        self.assertIn("download-step", result.node_outputs)
        node_res = result.node_outputs["download-step"]
        self.assertEqual(node_res["files"], ["/tmp/video_001.mp4", "/tmp/video_002.mp4"])
        self.assertEqual(node_res["folder"], "/tmp")
        self.assertEqual(node_res["metadata"]["title"], "Test YouTube Video")


if __name__ == "__main__":
    unittest.main()

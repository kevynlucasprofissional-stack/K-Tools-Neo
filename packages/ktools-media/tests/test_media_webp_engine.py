"""Engine-level tests for media.webp_to_png node."""
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


class MediaWebpEngineTests(unittest.TestCase):
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

    def test_workflow_execution(self):
        """Tests that webp_to_png node runs in a workflow context."""
        in_webp = self.root / "test.webp"
        in_webp.write_bytes(b"fake webp data")

        workflow = WorkflowDefinition(
            id="w_webp",
            nodes=[
                WorkflowNode(
                    id="n_in",
                    type="file.literal",
                    config={"path": str(in_webp)},
                ),
                WorkflowNode(
                    id="n_conv",
                    type="media.webp_to_png",
                    config={},
                ),
            ],
            edges=[
                WorkflowEdge("n_in", "file", "n_conv", "image"),
            ],
        )

        mock_img = MagicMock()
        mock_img.mode = "RGBA"

        def fake_save(path, fmt):
            Path(path).write_bytes(b"png data")

        mock_img.save.side_effect = fake_save

        mock_image_cm = MagicMock()
        mock_image_cm.__enter__ = lambda s: mock_img
        mock_image_cm.__exit__ = lambda s, *a: False

        with patch("ktools_media.image.webp_to_png.Image") as mock_image, \
             patch("ktools_media.image.webp_to_png.ImageOps") as mock_imageops:
            mock_image.open.return_value = mock_image_cm
            mock_imageops.exif_transpose.return_value = mock_img

            result = self.engine.execute(workflow)

        out_artifact = result.node_outputs["n_conv"]["image"]
        self.assertEqual(out_artifact.type, DataType.IMAGE)


if __name__ == "__main__":
    unittest.main()

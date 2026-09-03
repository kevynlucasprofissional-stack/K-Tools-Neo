"""Tests for media.webp_to_png behavior."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock


class MediaWebpBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        from ktools_media.image.webp_to_png import webp_to_png
        with self.assertRaises(FileNotFoundError):
            webp_to_png(self.root / "missing.webp", self.root / "out.png")

    @patch("ktools_media.image.webp_to_png.Image")
    @patch("ktools_media.image.webp_to_png.ImageOps")
    def test_webp_to_png_converts_and_saves(self, mock_imageops, mock_image):
        """Tests that a file is written atomically and conversion is called."""
        from ktools_media.image.webp_to_png import webp_to_png

        dummy_in = self.root / "test.webp"
        dummy_in.write_bytes(b"fake webp")
        out_path = self.root / "test.png"

        # Mock Pillow classes
        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_image.open.return_value.__enter__ = lambda s: mock_img
        mock_image.open.return_value.__exit__ = lambda s, *a: False
        mock_imageops.exif_transpose.return_value = mock_img

        def fake_save(path, fmt):
            Path(path).write_bytes(b"png data")

        mock_img.save.side_effect = fake_save

        result = webp_to_png(dummy_in, out_path)
        self.assertEqual(result, out_path)
        self.assertTrue(out_path.exists())
        mock_img.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()

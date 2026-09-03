import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.video.compress import compress_video

class MediaCompressBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.dummy_in = self.root / "in.mp4"
        self.dummy_in.write_bytes(b"dummy")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            compress_video(self.root / "missing.mp4", self.root / "out.mp4")

    @patch("ktools_media.video.compress.run_ffmpeg")
    def test_compress_video_args_and_atomic_replace(self, mock_run_ffmpeg):
        def fake_run_ffmpeg(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            
            tmp_out = Path(cmd[-1])
            tmp_out.write_bytes(b"compressed")
            return mock_res
            
        mock_run_ffmpeg.side_effect = fake_run_ffmpeg
        
        out_path = self.root / "out.mp4"
        res = compress_video(self.dummy_in, out_path, 30, "fast")
        
        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())
        
        cmd = mock_run_ffmpeg.call_args[0][0]
        self.assertIn("-crf", cmd)
        self.assertIn("30", cmd)
        self.assertIn("-preset", cmd)
        self.assertIn("fast", cmd)
        
if __name__ == '__main__':
    unittest.main()

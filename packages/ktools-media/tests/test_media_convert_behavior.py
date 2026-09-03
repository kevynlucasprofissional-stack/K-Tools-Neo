import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ktools_media.audio.convert import convert_audio


class MediaConvertBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.dummy_in = self.root / "in.wav"
        self.dummy_in.write_bytes(b"dummy")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            convert_audio(self.root / "missing.wav", self.root / "out.mp3", "mp3")

    @patch("ktools_media.audio.convert.run_ffmpeg")
    def test_convert_audio_args_and_atomic_replace(self, mock_run_ffmpeg):
        out_path = self.root / "out.mp3"
        
        def fake_run_ffmpeg(cmd, check=False):
            # cmd[-1] is the tmp_out
            tmp_out = Path(cmd[-1])
            tmp_out.write_bytes(b"converted")
            import subprocess
            return subprocess.CompletedProcess(cmd, 0, "", "")
            
        mock_run_ffmpeg.side_effect = fake_run_ffmpeg
        
        res = convert_audio(self.dummy_in, out_path, "mp3", "192k")
        
        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(out_path.read_bytes(), b"converted")
        
        # Check that it cleaned up tmp files
        tmps = list(self.root.glob("*.tmp"))
        self.assertEqual(len(tmps), 0)

        # Check ffmpeg args
        cmd = mock_run_ffmpeg.call_args[0][0]
        self.assertIn("-y", cmd)
        self.assertIn(str(self.dummy_in), cmd)
        self.assertIn("-b:a", cmd)
        self.assertIn("192k", cmd)


if __name__ == '__main__':
    unittest.main()

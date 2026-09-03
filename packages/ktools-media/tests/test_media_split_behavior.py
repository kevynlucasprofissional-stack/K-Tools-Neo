import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.audio.split import split_audio
from ktools_media.media_info import get_media_duration


class MediaSplitBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.dummy_in = self.root / "in.wav"
        self.dummy_in.write_bytes(b"dummy")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            split_audio(self.root / "missing.wav", self.root, 3)

    def test_invalid_parts_raises(self):
        with self.assertRaises(ValueError):
            split_audio(self.dummy_in, self.root, 1)

    @patch("ktools_media.audio.split.get_media_duration")
    @patch("ktools_media.audio.split.run_ffmpeg")
    def test_split_audio_args_and_atomic_replace(self, mock_run_ffmpeg, mock_get_duration):
        mock_get_duration.return_value = 30.0  # 30 seconds
        
        def fake_run_ffmpeg(cmd, **kwargs):
            tmp_out = Path(cmd[-1])
            tmp_out.write_bytes(b"split")
            mock_res = MagicMock()
            mock_res.returncode = 0
            return mock_res
            
        mock_run_ffmpeg.side_effect = fake_run_ffmpeg
        
        res = split_audio(self.dummy_in, self.root, 3, "mp3")
        
        self.assertEqual(len(res), 3)
        self.assertEqual(mock_run_ffmpeg.call_count, 3)
        
        # Check first part
        cmd1 = mock_run_ffmpeg.call_args_list[0][0][0]
        self.assertIn("-ss", cmd1)
        self.assertIn("0.000", cmd1)
        self.assertIn("-t", cmd1)
        self.assertIn("10.000", cmd1)
        
        # Check third part (no -t)
        cmd3 = mock_run_ffmpeg.call_args_list[2][0][0]
        self.assertIn("-ss", cmd3)
        self.assertIn("20.000", cmd3)
        self.assertNotIn("-t", cmd3)

if __name__ == '__main__':
    unittest.main()

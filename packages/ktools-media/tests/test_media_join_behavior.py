import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.audio.join import join_audios

class MediaJoinBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        
        self.audio1 = self.root / "1.mp3"
        self.audio1.write_bytes(b"dummy1")
        
        self.audio2 = self.root / "2.wav"
        self.audio2.write_bytes(b"dummy2")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            join_audios([self.audio1, self.root / "missing.mp3"], self.root / "out.m4a")

    def test_too_few_inputs_raises(self):
        with self.assertRaises(ValueError):
            join_audios([self.audio1], self.root / "out.m4a")

    @patch("ktools_media.audio.join.run_ffmpeg")
    def test_join_audio_args_and_atomic_replace(self, mock_run_ffmpeg):
        def fake_run_ffmpeg(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            
            # If it's the concat step, write the output file
            if "-f" in cmd and "concat" in cmd:
                tmp_out = Path(cmd[-1])
                # We need to write to it using an absolute path relative to the cwd? 
                # tmp_out is absolute in cmd[-1] because join.py does str(tmp_out) which is absolute!
                tmp_out.write_bytes(b"joined")
            else:
                # If it's a WAV conversion
                wav_out = Path(cmd[-1])
                wav_out.write_bytes(b"wav")
                
            return mock_res
            
        mock_run_ffmpeg.side_effect = fake_run_ffmpeg
        
        out_path = self.root / "out.mp3"
        res = join_audios([self.audio1, self.audio2], out_path, "mp3")
        
        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(mock_run_ffmpeg.call_count, 3) # 2 wav converts + 1 concat
        
        concat_cmd = mock_run_ffmpeg.call_args_list[2][0][0]
        self.assertIn("concat", concat_cmd)
        
if __name__ == '__main__':
    unittest.main()

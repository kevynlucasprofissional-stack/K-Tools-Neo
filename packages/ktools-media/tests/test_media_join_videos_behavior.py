import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.video.join import join_videos


class MediaJoinVideosBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.video1 = self.root / 'v1.mp4'
        self.video1.write_bytes(b'video1_data')

        self.video2 = self.root / 'v2.mp4'
        self.video2.write_bytes(b'video2_data')

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            join_videos([self.video1, self.root / 'missing.mp4'], self.root / 'out.mp4')

    def test_too_few_inputs_raises(self):
        with self.assertRaises(ValueError):
            join_videos([self.video1], self.root / 'out.mp4')

    @patch('ktools_media.video.join.run_ffmpeg')
    def test_fast_copy_success(self, mock_run_ffmpeg):
        def fake_run_ffmpeg(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ''
            tmp_out = Path(cmd[-1])
            tmp_out.write_bytes(b'joined_fast_video')
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run_ffmpeg

        out_path = self.root / 'out.mp4'
        res = join_videos([self.video1, self.video2], out_path, fast_copy=True)

        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(mock_run_ffmpeg.call_count, 1)
        self.assertIn('-c', mock_run_ffmpeg.call_args[0][0])
        self.assertIn('copy', mock_run_ffmpeg.call_args[0][0])

    @patch('ktools_media.video.join.run_ffmpeg')
    def test_fallback_normalization_when_fast_copy_fails(self, mock_run_ffmpeg):
        call_count = 0

        def fake_run_ffmpeg(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_res = MagicMock()

            # First call is fast copy concat, make it fail
            if call_count == 1:
                mock_res.returncode = 1
                mock_res.stderr = 'codec mismatch error'
                return mock_res

            # Subsequent calls are normalization and then final concat
            mock_res.returncode = 0
            mock_res.stderr = ''
            tmp_out = Path(cmd[-1])
            tmp_out.write_bytes(b'normalized_or_final')
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run_ffmpeg

        out_path = self.root / 'out.mp4'
        res = join_videos([self.video1, self.video2], out_path, fast_copy=True)

        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())
        # 1 failed fast copy + 2 normalizations + 1 final concat = 4 calls
        self.assertEqual(mock_run_ffmpeg.call_count, 4)


if __name__ == '__main__':
    unittest.main()

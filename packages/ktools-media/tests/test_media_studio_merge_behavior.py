import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.audio.studio_merge import merge_audio_studio, natural_sort_key


class MediaStudioMergeBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Unsorted tracks to test natural sorting: track1, track2, track10
        self.t1 = self.root / "track1.mp3"
        self.t2 = self.root / "track2.mp3"
        self.t10 = self.root / "track10.mp3"
        self.t1.write_bytes(b"audio1")
        self.t2.write_bytes(b"audio2")
        self.t10.write_bytes(b"audio10")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_natural_sort_key(self):
        items = ["item10.mp3", "item2.mp3", "item1.mp3"]
        sorted_items = sorted(items, key=natural_sort_key)
        self.assertEqual(sorted_items, ["item1.mp3", "item2.mp3", "item10.mp3"])

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            merge_audio_studio([self.t1, self.root / "missing.mp3"], self.root / "out.m4a")

    def test_too_few_inputs_raises(self):
        with self.assertRaises(ValueError):
            merge_audio_studio([self.t1], self.root / "out.m4a")

    @patch("ktools_media.audio.studio_merge.run_ffmpeg")
    def test_merge_audio_studio_success_and_hash(self, mock_run_ffmpeg):
        def fake_run(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"merged_studio_audio_content")
            elif str(out_file).endswith(".wav"):
                out_file.write_bytes(b"wav_temp")
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run

        out_path = self.root / "final.m4a"
        res_path, metadata = merge_audio_studio(
            [self.t10, self.t1, self.t2],
            out_path,
            output_format="m4a",
            natural_sort=True,
            normalize_volume=False,
        )

        self.assertEqual(res_path, out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(metadata["item_count"], 3)
        self.assertIn("sha256", metadata)
        self.assertEqual(len(metadata["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

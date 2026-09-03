import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.orchestrators.subfolder_audio import extract_and_join_by_subfolder


class MediaSubfolderAudioBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create two subfolders with videos
        self.mod1 = self.root / "Module_01"
        self.mod2 = self.root / "Module_02"
        self.mod1.mkdir(parents=True)
        self.mod2.mkdir(parents=True)

        (self.mod1 / "aula_02.mp4").write_bytes(b"vid1_2")
        (self.mod1 / "aula_01.mp4").write_bytes(b"vid1_1")
        (self.mod2 / "aula_01.mkv").write_bytes(b"vid2_1")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_root_raises(self):
        with self.assertRaises(FileNotFoundError):
            extract_and_join_by_subfolder(self.root / "missing_folder")

    @patch("ktools_media.audio.studio_merge.run_ffmpeg")
    @patch("ktools_media.orchestrators.subfolder_audio.run_ffmpeg")
    def test_extract_and_join_groups_and_produces_audio_per_subfolder(self, mock_run_sub, mock_run_studio):
        def fake_run(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"subfolder_audio_content")
            elif str(out_file).endswith(".wav"):
                out_file.write_bytes(b"wav_extracted")
            return mock_res

        mock_run_sub.side_effect = fake_run
        mock_run_studio.side_effect = fake_run

        out_dir = self.root / "output_audios"
        audio_files, report = extract_and_join_by_subfolder(
            root_dir=self.root,
            output_dir=out_dir,
            output_format="m4a",
        )

        self.assertEqual(len(audio_files), 2)
        for a in audio_files:
            self.assertTrue(a.exists())

        self.assertEqual(report["total_folders_processed"], 2)
        self.assertEqual(report["total_videos_processed"], 3)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.audio.deesser import deess_audio


class MediaDeesserBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.audio = self.root / "sample.wav"
        self.audio.write_bytes(b"RIFFsample_audio")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            deess_audio(self.root / "missing.wav", self.root / "out.wav")

    def test_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            deess_audio(self.audio, self.root / "out.wav", intensity=1.5)
        with self.assertRaises(ValueError):
            deess_audio(self.audio, self.root / "out.wav", frequency=-0.1)

    @patch("ktools_media.audio.deesser.run_ffmpeg")
    def test_deess_audio_filter_command_and_atomic_replace(self, mock_run_ffmpeg):
        def fake_run(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"deessed_audio_bytes")
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run

        out_path = self.root / "clean.wav"
        res = deess_audio(
            self.audio,
            out_path,
            intensity=0.7,
            frequency=0.6,
            noise_reduction=True,
            output_format="wav",
        )

        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())

        cmd = mock_run_ffmpeg.call_args[0][0]
        # Check that -af with deesser filter was applied
        self.assertIn("-af", cmd)
        af_arg = cmd[cmd.index("-af") + 1]
        self.assertIn("deesser", af_arg)
        self.assertIn("afftdn", af_arg)


if __name__ == "__main__":
    unittest.main()

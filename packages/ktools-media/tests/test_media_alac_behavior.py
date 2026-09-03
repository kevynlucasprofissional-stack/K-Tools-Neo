import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from ktools_media.audio.alac import convert_to_alac, compute_decoded_pcm_hash


class MediaAlacBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.wav = self.root / "test.wav"
        self.wav.write_bytes(b"RIFFfake_wav_data")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_input_raises(self):
        with self.assertRaises(FileNotFoundError):
            convert_to_alac(self.root / "missing.wav", self.root / "out.m4a")

    @patch("ktools_media.audio.alac.run_ffmpeg")
    def test_convert_to_alac_with_verification(self, mock_run_ffmpeg):
        # We need mock_run_ffmpeg to handle:
        # 1. conversion command: -c:a alac
        # 2. compute hash of input (pcm dump)
        # 3. compute hash of output (pcm dump)
        def fake_run(cmd, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"fake_alac_m4a_data")
            elif "-f" in cmd and "s16le" in cmd:
                # PCM dump
                out_file.write_bytes(b"identical_pcm_bytes_12345678")
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run

        out_path = self.root / "out.m4a"
        res_path, pcm_hash = convert_to_alac(self.wav, out_path, verify=True)

        self.assertEqual(res_path, out_path)
        self.assertTrue(out_path.exists())
        self.assertIsNotNone(pcm_hash)
        self.assertEqual(len(pcm_hash), 64)  # valid SHA-256 hex string

    @patch("ktools_media.audio.alac.run_ffmpeg")
    def test_convert_to_alac_verification_mismatch_raises(self, mock_run_ffmpeg):
        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            out_file = Path(cmd[-1])
            if str(out_file).endswith(".tmp"):
                out_file.write_bytes(b"fake_alac_m4a_data")
            elif "-f" in cmd and "s16le" in cmd:
                # Return different PCM bytes to simulate corrupted / lossy conversion
                out_file.write_bytes(f"pcm_bytes_call_{call_count}".encode())
            return mock_res

        mock_run_ffmpeg.side_effect = fake_run

        out_path = self.root / "out_mismatch.m4a"
        with self.assertRaises(RuntimeError) as ctx:
            convert_to_alac(self.wav, out_path, verify=True)
        self.assertIn("verification failed", str(ctx.exception).lower())
        self.assertFalse(out_path.exists())  # temporary file cleaned up


if __name__ == "__main__":
    unittest.main()

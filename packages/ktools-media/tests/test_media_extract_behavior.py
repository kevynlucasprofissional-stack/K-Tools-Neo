from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from ktools_core.models import DataType
from ktools_media.api import MediaExtractionError, extract_audio_from_video
from ktools_media.ffmpeg import get_ffmpeg_exe


class MediaExtractBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        # We need a small valid video file with audio to test extraction.
        # Since we don't have one checked in, we will create a synthetic one using ffmpeg!
        self.video_path = self.root / "synthetic_test_video.mp4"
        self._create_synthetic_video()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create_synthetic_video(self) -> None:
        import subprocess
        exe = get_ffmpeg_exe()
        # Create a 1-second video with a 440Hz sine wave audio
        cmd = [
            exe,
            "-y",
            "-f", "lavfi", "-i", "color=c=black:s=128x128:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(self.video_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def test_extract_audio_success(self) -> None:
        output_path = self.root / "out.m4a"
        artifact = extract_audio_from_video(self.video_path, output_path, format="m4a")
        
        self.assertTrue(output_path.exists())
        self.assertEqual(artifact.type, DataType.AUDIO)
        self.assertEqual(artifact.mime_type, "audio/mp4")
        self.assertEqual(artifact.metadata["name"], "out.m4a")
        self.assertGreater(artifact.metadata["size"], 0)

    def test_extract_audio_missing_stream(self) -> None:
        # Create a video without audio
        import subprocess
        exe = get_ffmpeg_exe()
        no_audio_path = self.root / "no_audio.mp4"
        cmd = [
            exe,
            "-y",
            "-f", "lavfi", "-i", "color=c=black:s=128x128:d=1",
            "-c:v", "libx264",
            str(no_audio_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        output_path = self.root / "out.m4a"
        with self.assertRaises(MediaExtractionError) as ctx:
            extract_audio_from_video(no_audio_path, output_path, format="m4a")
        self.assertIn("does not have a detectable audio stream", str(ctx.exception))

    def test_extract_audio_same_input_output(self) -> None:
        with self.assertRaises(MediaExtractionError) as ctx:
            extract_audio_from_video(self.video_path, self.video_path, format="mp4")
        self.assertIn("cannot be the same as input", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

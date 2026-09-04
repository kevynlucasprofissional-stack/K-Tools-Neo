import unittest
from pathlib import Path

from ktools_youtube.engine.adapter import YtDlpAdapter, detect_js_runtimes


class TestYtDlpAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = YtDlpAdapter(ffmpeg_path="/bin/fake-ffmpeg")

    def test_build_video_options(self):
        opts = self.adapter.build_options(
            media_type="video",
            quality="1080p",
            output_dir=Path("/tmp/downloads"),
        )
        self.assertIn("1080", opts["format"])
        self.assertEqual(opts["merge_output_format"], "mp4")
        self.assertEqual(opts["ffmpeg_location"], "/bin/fake-ffmpeg")

    def test_build_audio_options(self):
        opts = self.adapter.build_options(
            media_type="audio",
            audio_format="mp3",
            output_dir=Path("/tmp/downloads"),
        )
        self.assertEqual(opts["format"], "bestaudio/best")
        postprocessors = opts.get("postprocessors", [])
        self.assertTrue(any(p.get("preferredcodec") == "mp3" for p in postprocessors))

    def test_js_runtimes_configured_when_available(self):
        detected = detect_js_runtimes()
        opts = self.adapter.build_options()
        if detected:
            self.assertIn("js_runtimes", opts)


if __name__ == "__main__":
    unittest.main()

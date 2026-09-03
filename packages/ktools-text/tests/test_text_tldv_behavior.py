import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ktools_text.tldv import (
    TranscriptBlock,
    extract_tldv_transcript,
    export_transcript_outputs,
)

SAMPLE_TLDV_HTML = """
<!DOCTYPE html>
<html>
<body>
<div id="transcript-container">
    <p data-index="0">
        <div class="inline">Alice</div>
        <span data-speaker="false" data-time="1000">Hello</span>
        <span data-speaker="false" data-time="1500">everyone.</span>
    </p>
    <p data-index="1">
        <div class="inline">Bob</div>
        <span data-speaker="false" data-time="5000">Hi</span>
        <span data-speaker="false" data-time="5500">Alice!</span>
    </p>
</div>
</body>
</html>
"""


class TextTldvBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.html_file = self.root / "meeting.html"
        self.html_file.write_text(SAMPLE_TLDV_HTML, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_container_raises(self):
        invalid_html = "<html><body><div>No transcript</div></body></html>"
        with self.assertRaises(ValueError):
            extract_tldv_transcript(invalid_html)

    def test_extract_tldv_blocks(self):
        blocks = extract_tldv_transcript(SAMPLE_TLDV_HTML)
        self.assertEqual(len(blocks), 2)

        self.assertEqual(blocks[0].speaker, "Alice")
        self.assertEqual(blocks[0].text, "Hello everyone.")
        self.assertEqual(blocks[0].start_time_ms, 1000)

        self.assertEqual(blocks[1].speaker, "Bob")
        self.assertEqual(blocks[1].text, "Hi Alice!")
        self.assertEqual(blocks[1].start_time_ms, 5000)

    def test_export_transcript_outputs(self):
        blocks = extract_tldv_transcript(SAMPLE_TLDV_HTML)
        md_path, srt_path, json_data = export_transcript_outputs(
            blocks=blocks,
            output_dir=self.root,
            base_name="meeting",
            title="Team Sync",
        )

        self.assertTrue(md_path.exists())
        self.assertTrue(srt_path.exists())

        md_content = md_path.read_text(encoding="utf-8")
        self.assertIn("# Team Sync", md_content)
        self.assertIn("Alice", md_content)
        self.assertIn("Hello everyone.", md_content)

        srt_content = srt_path.read_text(encoding="utf-8")
        self.assertIn("00:00:01,000 -->", srt_content)
        self.assertIn("Alice: Hello everyone.", srt_content)

        self.assertEqual(len(json_data["blocks"]), 2)


if __name__ == "__main__":
    unittest.main()

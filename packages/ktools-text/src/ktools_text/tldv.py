from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


@dataclass
class TranscriptBlock:
    index: int
    start_time_ms: int
    end_time_ms: int
    speaker: str
    text: str


def ms_to_srt_stamp(ms: int) -> str:
    """Converts milliseconds to SRT timestamp: HH:MM:SS,mmm"""
    total_seconds = max(0, ms) // 1000
    milliseconds = max(0, ms) % 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def ms_to_stamp(ms: int) -> str:
    """Converts milliseconds to human timestamp: [HH:MM:SS]"""
    total_seconds = max(0, ms) // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"


class _TldvHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found_container = False
        self.in_container = False
        self.container_depth = 0

        self.current_p_index: Optional[int] = None
        self.in_p = False

        self.in_speaker_tag = False
        self.current_speaker = ""

        self.in_word_span = False
        self.current_word_time: Optional[int] = None
        self.current_words: list[tuple[int, str]] = []

        self.blocks: list[TranscriptBlock] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if attr_dict.get("id") == "transcript-container":
            self.found_container = True
            self.in_container = True
            self.container_depth = 1
            return

        if self.in_container:
            self.container_depth += 1

            if tag == "p" and "data-index" in attr_dict:
                self.in_p = True
                try:
                    self.current_p_index = int(attr_dict["data-index"])
                except ValueError:
                    self.current_p_index = len(self.blocks)
                self.current_speaker = ""
                self.current_words = []

            elif self.in_p:
                classes = attr_dict.get("class", "").split()
                if tag == "div" and "inline" in classes:
                    self.in_speaker_tag = True
                elif tag == "span" and attr_dict.get("data-speaker") == "false":
                    self.in_word_span = True
                    try:
                        self.current_word_time = int(attr_dict.get("data-time", "0"))
                    except ValueError:
                        self.current_word_time = 0

    def handle_endtag(self, tag: str):
        if not self.in_container:
            return

        if tag == "p" and self.in_p:
            self.in_p = False
            if self.current_words:
                start_time = self.current_words[0][0]
                end_time = self.current_words[-1][0] + 1000
                text = " ".join(w for _, w in self.current_words).strip()
                self.blocks.append(
                    TranscriptBlock(
                        index=self.current_p_index if self.current_p_index is not None else len(self.blocks),
                        start_time_ms=start_time,
                        end_time_ms=end_time,
                        speaker=self.current_speaker.strip() or "Speaker",
                        text=text,
                    )
                )
        elif tag == "div" and self.in_speaker_tag:
            self.in_speaker_tag = False
        elif tag == "span" and self.in_word_span:
            self.in_word_span = False
            self.current_word_time = None

        self.container_depth -= 1
        if self.container_depth <= 0:
            self.in_container = False

    def handle_data(self, data: str):
        if not self.in_p:
            return
        if self.in_speaker_tag:
            self.current_speaker += data
        elif self.in_word_span:
            cleaned = data.strip()
            if cleaned and self.current_word_time is not None:
                self.current_words.append((self.current_word_time, cleaned))


def extract_tldv_transcript(html_content: str) -> list[TranscriptBlock]:
    """
    Parses tl;dv HTML content looking for #transcript-container and extracts
    structured TranscriptBlock instances.
    """
    parser = _TldvHTMLParser()
    parser.feed(html_content)
    if not parser.found_container:
        raise ValueError("No transcript-container found in HTML content.")

    return parser.blocks


def export_transcript_outputs(
    blocks: list[TranscriptBlock],
    output_dir: Path,
    base_name: str,
    title: Optional[str] = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Exports transcript blocks to Markdown, SRT subtitles, and structured JSON.
    Writes files atomically using temporary files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_base = base_name.replace(".html", "").replace(".htm", "")
    doc_title = title or clean_base.replace("_", " ").title()

    md_path = output_dir / f"{clean_base}.md"
    srt_path = output_dir / f"{clean_base}.srt"

    tmp_md = md_path.with_name(f"{md_path.name}.{uuid4().hex}.tmp")
    tmp_srt = srt_path.with_name(f"{srt_path.name}.{uuid4().hex}.tmp")

    # 1. Build Markdown
    md_lines: list[str] = [f"# {doc_title}\n\n"]
    for b in blocks:
        stamp = ms_to_stamp(b.start_time_ms)
        md_lines.append(f"### {stamp} {b.speaker}\n\n{b.text}\n\n")

    # 2. Build SRT
    srt_lines: list[str] = []
    for i, b in enumerate(blocks, start=1):
        start_stamp = ms_to_srt_stamp(b.start_time_ms)
        end_stamp = ms_to_srt_stamp(b.end_time_ms)
        srt_lines.append(f"{i}\n{start_stamp} --> {end_stamp}\n{b.speaker}: {b.text}\n\n")

    try:
        tmp_md.write_text("".join(md_lines), encoding="utf-8")
        tmp_srt.write_text("".join(srt_lines), encoding="utf-8")

        os.replace(tmp_md, md_path)
        os.replace(tmp_srt, srt_path)
    finally:
        for t in (tmp_md, tmp_srt):
            if t.exists():
                try:
                    t.unlink()
                except OSError:
                    pass

    json_payload: dict[str, Any] = {
        "title": doc_title,
        "total_blocks": len(blocks),
        "blocks": [asdict(b) for b in blocks],
    }

    return md_path, srt_path, json_payload

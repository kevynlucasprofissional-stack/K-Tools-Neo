# Discovery: Text tl;dv Extract Node V1

## Context and Problem
The repository contains `Extrator TLDV.py`, which parses exported HTML files from the tl;dv meeting recording platform, extracts transcript blocks (speakers, timestamps, and dialog), and converts them to TXT, Markdown, SRT subtitles, and JSON.

Currently, `packages/ktools-text` contains merge and split nodes for raw text/Markdown. Adding `text.tldv_extract` provides document intelligence for meeting transcripts, enabling automated documentation generation, subtitle generation, and AI summarization workflows.

## Candidate Node Definition
- Node Type: `text.tldv_extract`
- Inputs: `html: FILE` (the exported tl;dv HTML file)
- Outputs:
  - `markdown: FILE` (formatted Markdown transcript)
  - `srt: FILE` (SRT subtitle file with timestamped captions)
  - `json: JSON` (structured JSON data containing list of transcript blocks)
- Config:
  - `title` (optional str)
  - `output_dir` (optional str)

## Technical Architecture
- Module: `packages/ktools-text/src/ktools_text/tldv.py`
- Parser: Implemented with standard library `html.parser.HTMLParser` (with optional `bs4` support if present), avoiding any external dependencies in CI.
- Outputs written atomically via `.tmp` promotion.
- Integrated into `ktools-text` node registry.

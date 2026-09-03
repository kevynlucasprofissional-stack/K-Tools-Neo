# ADR 043: Text tl;dv Extract Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `Extrator TLDV.py` which parsed saved tl;dv meeting HTML pages, extracting timestamps, speaker tags, and utterances into multiple text formats.
Migrating this into `ktools-text` unlocks transcript intelligence and meeting documentation workflows.

## Decision
- Implement `text.tldv_extract` in `ktools-text`.
- Pure Python standard library `html.parser.HTMLParser` implementation that traverses `#transcript-container` and parses speakers (`div.inline`) and words (`span[data-time][data-speaker=false]`).
- Zero external package dependencies (no bs4 requirement).
- Emits three outputs:
  - `markdown`: formatted Markdown document with headings per timestamp/speaker.
  - `srt`: SubRip subtitle file with standard `HH:MM:SS,mmm` timecodes.
  - `json`: structured payload with all block metadata.
- Atomic file writing via `.tmp` promotion.

## Consequences
- Clean, fast, zero-dependency transcript extraction directly inside K-Tools workflows.

# M5 Extension: Text tl;dv Extract Node V1

## What was done
- Implemented `text.tldv_extract` node migrating `Extrator TLDV.py`.
- Built pure standard-library HTML parser extracting speech blocks, timestamps, and speakers without external dependencies.
- Emits Markdown, SRT subtitles, and structured JSON.
- Added behavior unit tests and engine workflow integration tests.
- All 32 tests in `ktools-text` passing.

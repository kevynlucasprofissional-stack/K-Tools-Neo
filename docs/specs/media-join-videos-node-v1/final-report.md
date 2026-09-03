# M5 Extension: Media Join Videos Node V1

## What was done
- Implemented `media.join_videos` node migrating `JV.py`.
- Implemented fast-copy concat demuxer with automatic fallback normalization for mismatched codecs.
- Atomic file publication via `.tmp` promotion.
- Integrated into node registry and covered with behavior and engine diagnostics tests.

## Verification
- 4 behavior unit tests + 1 engine workflow integration test passing.
- Total 33/33 tests passing in `ktools-media`.

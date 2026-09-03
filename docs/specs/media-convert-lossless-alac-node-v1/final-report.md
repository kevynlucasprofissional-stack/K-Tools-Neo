# M5 Extension: Media Convert Lossless ALAC Node V1

## What was done
- Implemented `media.convert_lossless_alac` node migrating `wav_para_m4a_lossless_gui_v2.py`.
- Encapsulated ALAC encoding with decoded PCM SHA-256 bit-exact verification.
- Output metadata captures hash proof and verification status.
- Covered with unit behavior tests (including fail-closed mismatch check) and engine diagnostics tests.

## Verification
- 3 behavior tests + 1 engine workflow test passing.
- Total 37/37 tests passing in `ktools-media`.

# ADR 039: Media Convert Lossless ALAC Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The workspace contained `wav_para_m4a_lossless_gui_v2.py` which provides bit-verifiable WAV to Apple Lossless Audio Codec (ALAC) `.m4a` conversion. In preservation and high-fidelity production environments, verifying that no loss or distortion occurred during transcoding is mandatory.

## Decision
- Implement `media.convert_lossless_alac` node in `ktools-media`.
- Uses FFmpeg with `-c:a alac` in `.m4a` container.
- Optional but default-on `verify_bit_exact`: decodes both the source file and the resulting ALAC `.m4a` into raw 16-bit little-endian PCM streams, and compares their SHA-256 hashes.
- If hashes mismatch, raises `RuntimeError` and purges the temporary output to fail closed.
- If verified, sets `pcm_sha256` and `verified_bit_exact: true` in the output artifact metadata.
- Atomic file publication via `.tmp` promotion.

## Consequences
- Archive and mastering workflows can guarantee 100% mathematical lossless fidelity.
- Subprocesses remain fully observed in `DiagnosticsSession`.

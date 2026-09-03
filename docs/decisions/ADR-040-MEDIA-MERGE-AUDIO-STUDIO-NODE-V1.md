# ADR 040: Media Merge Audio Studio Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `Audio Merge Studio V2.py` which allowed selecting audio and video files, naturally sorting tracks, normalizing volume levels, and generating final combined audio files with integrity validation.

## Decision
- Implement `media.merge_audio_studio` node in `ktools-media`.
- Takes `FILE_SET` of audio/video sources and produces a unified `AUDIO` artifact.
- Built-in `natural_sort_key` to sort alphanumerically (`1, 2, 10`).
- Normalizes all sources to 44.1kHz stereo WAV before concat demuxing, seamlessly handling mixed video/audio tracks.
- Optional loudness normalization via FFmpeg `loudnorm`.
- Computes SHA-256 integrity hash of final file.
- Atomic file replacement via `.tmp`.

## Consequences
- High-level studio audio aggregation is available as a node in workflows.
- Fully compatible with `imageio-ffmpeg` and tracked in `DiagnosticsSession`.

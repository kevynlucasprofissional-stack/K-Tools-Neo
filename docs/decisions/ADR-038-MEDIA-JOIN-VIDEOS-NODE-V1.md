# ADR 038: Media Join Videos Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `JV.py` ("Unificador de Vídeos Sequenciais") using `moviepy`, and legacy `join_video_files` using FFmpeg. Video concatenation is a core requirement for sequence assembly and batch multimedia workflows.

## Decision
- Implement `media.join_videos` in `ktools-media` using FFmpeg.
- Two-stage strategy: fast stream copy concat (`-c copy`), falling back to audio/video normalization (`libx264`/`aac` with `scale=trunc(iw/2)*2:trunc(ih/2)*2`) if stream copy fails.
- Node takes `FILE_SET` of videos and outputs a single `VIDEO` artifact.
- Atomic publication via temporary file and `os.replace`.
- All subprocesses logged via `run_ffmpeg` in `DiagnosticsSession`.

## Consequences
- Clean FFmpeg implementation with zero dependency on `moviepy`.
- Full compatibility with the existing `imageio-ffmpeg` packaging.

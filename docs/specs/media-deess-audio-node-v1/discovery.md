# Discovery: Media De-ess Audio Node V1

## Context and Problem
The workspace contains `removedor_sibilancia_gui_v2.py`, which provides dynamic sibilance removal (attenuating harsh "s", "x", "ch", "sh" voice sounds) and noise reduction.
In automated speech processing, podcast mastering, and AI voice pipeline ingestion, sibilance causes harsh distortion and ear fatigue.

## Candidate Node Definition
- Node Type: `media.deess_audio`
- Inputs: `audio: FILE` (audio or video artifact)
- Outputs: `audio: AUDIO`
- Config:
  - `intensity` (float, default 0.5): De-essing intensity from 0.0 (subtle) to 1.0 (aggressive).
  - `frequency` (float, default 0.5): Center frequency control (0.0 to 1.0, where 0.5 corresponds to ~6kHz).
  - `noise_reduction` (bool, default False): Apply spectral noise reduction / highpass gating.
  - `output_format` (str, default "wav")
  - `output_dir` (optional str)

## Technical Architecture
- Module: `packages/ktools-media/src/ktools_media/audio/deesser.py`
- Primary engine: FFmpeg's native `deesser` and `afftdn` (audio FFT denoiser) filters via `run_ffmpeg`. This guarantees cross-platform reliability on Windows, Ubuntu, and macOS without requiring heavy scientific C-extensions (`scipy`/`noisereduce`) in CI.
- Optional DSP fallback when `scipy` is present.
- Atomic file replacement via `.tmp`.
- Tracked in `DiagnosticsSession`.

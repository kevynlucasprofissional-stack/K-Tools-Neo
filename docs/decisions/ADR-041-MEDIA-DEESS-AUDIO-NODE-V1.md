# ADR 041: Media De-ess Audio Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `removedor_sibilancia_gui_v2.py` for sibilance removal and noise reduction. Sibilant sounds ("s", "x", "ch", "sh") in vocal tracks require attenuation before downstream mixing or speech-to-text processing.

## Decision
- Implement `media.deess_audio` node in `ktools-media`.
- Uses FFmpeg's specialized `deesser` filter with configurable `intensity` and `frequency`, plus optional `afftdn` spectral denoiser.
- Avoids strict runtime dependencies on heavy scientific libraries (`scipy`/`noisereduce`) while delivering deterministic results in both Linux and Windows environments.
- Node takes a `FILE` artifact and outputs an `AUDIO` artifact.
- Atomic file publication via `.tmp`.
- All subprocesses tracked in `DiagnosticsSession`.

## Consequences
- Voice processing pipelines can now clean vocal tracks inside K-Tools workflows without external DAW tools.

# ADR 031: Media Extract Audio Node V1

**Date**: 2026-09-02
**Status**: Accepted
**Context**: Milestone 5 (Media extraction)

## Context

The legacy `K Tools Neo` script contained an integration with FFmpeg to extract and compress audio and video. In our modern architecture, all media manipulation must run as proper `CachePolicy.NEVER` nodes because they write non-deterministic artifacts to the disk (unless we implement content-addressed blob storage).

We needed to establish the foundational rules for `ktools-media` package:
1. Ensure FFmpeg is available natively across platforms without relying on system packages.
2. Comply with the M3 observability rules, which dictate that every external subprocess call must be recorded in the `DiagnosticsSession` to be included in the support bundle.

## Decision

1. **Dependency**: We use `imageio-ffmpeg>=0.4.0` in the `ktools-media` package. It dynamically downloads the correct FFmpeg/FFprobe binaries for the host system if they are not already installed or available on PATH.
2. **Subprocess Recording**: We extended `ktools_core.diagnostics` to include a global `ContextVar` that exposes the `_ACTIVE_SESSION`. We added a `record_subprocess` helper that mimics `subprocess.run` but automatically wraps the call in `session.run_subprocess` when an active diagnostic session exists. This allows deeply nested functional core modules to trace subprocesses without threading context everywhere.
3. **Artifact Atomicity**: Audio extraction generates a temporary file and atomically replaces it using `os.replace` to guarantee that partial files from aborted FFmpeg runs are never read by subsequent nodes.
4. **Cache Policy**: `CachePolicy.NEVER`.
5. **Fallback Probe**: If `imageio-ffmpeg` fails to supply an `ffprobe` executable (which happens on some older environments or specific versions), the capability gracefully falls back to parsing `ffmpeg -i` stderr to detect streams.

## Consequences

- The `ktools-media` package is now the designated boundary for media-related work.
- We have a reusable `run_ffmpeg` and `run_ffprobe` abstraction that can be used for upcoming slices (e.g., video compression, PNG to ICO).
- CI now tests `ktools-media` separately.

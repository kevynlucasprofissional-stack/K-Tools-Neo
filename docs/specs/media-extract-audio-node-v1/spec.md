# Spec — Media Extract Audio Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 Slice 9
Canonical implementation target: `packages/ktools-media/`

## Objective

Extract the smallest bounded media capability from the legacy monolith to establish the reusable FFmpeg/FFprobe process foundation: audio extraction from video.

The slice must define a safe `subprocess` boundary integrated with M3 structured diagnostics, use explicit dependency management for FFmpeg (`imageio-ffmpeg`), return strongly-typed `AUDIO` artifacts, and handle multi-format encoding (`wav`, `mp3`, `aac`, `m4a`, `flac`) while preventing unconstrained Media extraction from repeating legacy design debt.

## Fresh candidate decision

Slice 9 fresh discovery compared at minimum:
- bounded Files/Folders operations (already resolved in Slice 8);
- the smallest useful Media capability (Extract Audio from Video);
- PNG→ICO (image utility);
- PDF compression (document utility).

**Media Extract Audio V1** is selected.

Reasons:
1. Media forms the last major capability family present in the legacy monolith (audio join, split, cut, extraction, and video join).
2. The foundation of executing `ffmpeg` and `ffprobe` natively is an infrastructural risk. Establishing a safe, diagnostic-integrated process boundary for FFmpeg is required before we can tackle broader audio/video workflows.
3. Extracting audio from video naturally composes with File/Folder discovery (Slice 8).
4. PNG→ICO and PDF compression are useful but have lower structural/architectural impact compared to the FFmpeg boundary.

## Scope boundary

This slice owns:
- FFmpeg/FFprobe location and execution boundary.
- Media duration probing via FFprobe with FFmpeg fallback.
- Audio stream detection.
- Audio extraction to common formats (mp3, m4a/aac, wav, flac).

It does not own:
- Video joining or processing.
- Advanced audio filtering (noise reduction, etc.).
- Audio file concatenation.

## Package boundary

Create official package:

```text
packages/ktools-media/
```

Runtime dependencies:

```text
ktools-core
imageio-ffmpeg>=0.4.0
```

## Production node contract

Node type:

```text
media.extract_audio
```

Version `1`.

Ports:

```text
video: FILE -> audio: AUDIO
```

Cache policy:

```text
NEVER
```

Config:
```json
{
  "format": "m4a", // wav, mp3, aac, m4a, flac
  "bitrate": "192k" // optional, defaults to sensible values based on format
}
```

The node validates the video has an audio stream, extracts it using `ffmpeg -vn`, and saves the file via a temporary atomic path publication, outputting an `AUDIO` artifact.
Why NEVER: Generating media side-effects to disk cannot be skipped without a proved replay mechanism, following the invariant established in M4.

## Canonical capability owner

One business-logic owner:

```python
ktools_media.audio.extract.extract_audio_from_video(
    video_path: Path,
    output_path: Path,
    format: str,
    bitrate: str | None = None,
    context: NodeExecutionContext | None = None,
) -> Artifact
```

## Diagnostics

The `ktools_media` execution wrapper MUST use `ktools_core.diagnostics.record_subprocess` for every FFmpeg/FFprobe call, ensuring full observability (command line, stdout, stderr, exit code, duration) in the M3 Support Bundle.

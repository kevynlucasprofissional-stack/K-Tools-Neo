# Plan / Design — Media Extract Audio Node V1

## 1. Spec
`docs/specs/media-extract-audio-node-v1/spec.md`

## 2. Approach
1. Create `ktools-media` package with `imageio-ffmpeg` dependency.
2. Implement `ktools_media.ffmpeg` to provide `run_ffmpeg` and `run_ffprobe` wrapping `subprocess.run` and `record_subprocess` from `ktools_core.diagnostics`.
3. Implement `ktools_media.audio.extract.extract_audio_from_video` taking the source file and writing to a temporary file before renaming (atomic temp-to-promote publication).
4. Extract audio logic uses `media_has_audio_stream` to fail fast if no audio is present.
5. Create `media.extract_audio` node adapting the Python API.
6. Return `AUDIO` artifact with `mime_type` and `produced_by` provenance.

## 3. Current inspected state
The legacy monolith handles FFmpeg via `get_ffmpeg_exe()` calling `imageio_ffmpeg` and uses `subprocess.run` directly with manual error capturing. We will centralize this safely.

## 4. Architecture
```text
WorkflowEngine
    │
media.extract_audio
    │
ktools_media.audio.extract
    │
ktools_media.ffmpeg (observability boundary)
    │
subprocess (imageio-ffmpeg)
```

## 5. State ownership
| State | Owner | Lifetime | Persistence | Recovery |
|---|---|---|---|---|
| Audio output file | `extract_audio_from_video` | Durable | FS | M4 Cache/Retry |
| Subprocess logs | `record_subprocess` | Run | SQLite/JSONL | M3 Support Bundle |

## 6. Validation strategy
- RED: Test asserting absence of `ktools_media` modules.
- GREEN: Implement the package, the FFmpeg wrapper, and the node.
- SMOKE: Download/generate a tiny valid video file with an audio track in CI (or use ffmpeg to create a synthetic one), then run the `media.extract_audio` node and verify the resulting audio file.

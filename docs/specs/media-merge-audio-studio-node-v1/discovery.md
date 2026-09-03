# Discovery: Media Merge Audio Studio Node V1

## Context and Problem
The workspace contains `Audio Merge Studio V2.py`, a dedicated application for merging audio (and extracting from video when necessary) with:
1. Natural alphanumeric ordering (`track1`, `track2`, `track10`).
2. Robust support for mixed audio/video inputs.
3. Audio loudness / peak analysis and volume normalization.
4. Final file SHA-256 integrity digest and metadata reporting.

Existing `media.join_audios` handles primitive audio concatenation via WAV normalization, but lacks natural sorting, video source tolerance, volume normalization, and integrity hashes.

## Candidate Node Definition
- Node Type: `media.merge_audio_studio`
- Inputs: `sources: FILE_SET` (list of Audio or Video Artifacts)
- Outputs: `audio: AUDIO`
- Config:
  - `format` (str, default "m4a")
  - `bitrate` (optional str, default "192k")
  - `normalize_volume` (bool, default False)
  - `natural_sort` (bool, default True)
  - `output_name` (optional str)
  - `output_dir` (optional str)

## Technical Architecture
- Module: `packages/ktools-media/src/ktools_media/audio/studio_merge.py`
- Functions:
  - `natural_sort_key(text: str)`
  - `merge_audio_studio(sources: Sequence[Path], output_path: Path, ...) -> tuple[Path, dict[str, Any]]`
- Atomic replacement and M3 diagnostics compliance.

# Spec: Media Convert Audio Node V1

## Context

Continuing M5 Media Capabilities, we replace the legacy `convert_audio_files_batch` behavior. The legacy script converted a batch of audio files into specific formats (MP3, M4A, WAV, FLAC, AAC, OGG) with customizable bitrates (96k to 320k, or Automatic).

In `K-Tools-Neo`, orchestration (batching) is handled by the graph engine. Thus, our base primitive will be a node that converts a *single* audio artifact.

## Node: `media.convert_audio`

**Type Name**: `media.convert_audio`
**Cache Policy**: `NEVER` (Because it interacts with the host filesystem to write the converted artifact, and our engine currently relies on literal output paths). Wait, if the user doesn't provide an output path, does the node generate one? Yes, using `ktools_core.registry.Workspace`. But writing file data on disk is considered a side-effect on the environment. `NEVER` cache policy ensures it always executes.

### Inputs
- `audio` (`DataType.AUDIO`): The source audio artifact.
- `output_format` (`DataType.STRING`): The target format, restricted to `['mp3', 'm4a', 'wav', 'flac', 'aac', 'ogg']`.
- `bitrate` (`DataType.STRING`, optional): Target bitrate (e.g. `192k`, `320k`). If not provided, FFmpeg decides automatically (or copies default).
- `output_dir` (`DataType.STRING`, optional): Target directory. If omitted, uses a temporary workspace.

### Outputs
- `audio` (`DataType.AUDIO`): The converted artifact.

## Behavior Rules

1. **Validation**: Check that the input audio exists and is a valid file.
2. **Subprocess Tracking**: The conversion must use `ktools_media.ffmpeg.run_ffmpeg()` so it records standard output and exit codes for M3 diagnostics via the `DiagnosticsSession`.
3. **Atomic Writes**: `ffmpeg` should write to `[target_path].tmp` and then `os.replace` the file to `[target_path]` to prevent partial or corrupt files from entering the pipeline if execution is aborted.
4. **Collision Avoidance**: If `output_dir` is provided and a file with the same name exists, the node should append a suffix or UUID to avoid overwriting unless configured otherwise.

## Hand-off Checklist

- [ ] Add `convert_audio` capability to `ktools_media.audio.convert`.
- [ ] Define the `media.convert_audio` node contract.
- [ ] Write behavior unit tests (`test_media_convert_behavior.py`).
- [ ] Write engine execution tests (`test_media_convert_engine.py`) to verify it records diagnostics and handles atomic writes.
- [ ] Update `ROADMAP.md` and `CURRENT.md` to reflect Slice 10 progress.

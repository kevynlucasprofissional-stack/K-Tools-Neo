# Spec: Media Split Audio Node V1

## Context

Continuing M5 Media Capabilities, we adapt the legacy _audio_split_run feature. The legacy logic divides a given audio file into N parts of equal length. For workflow purposes, this will be represented as a Node that takes a source audio file and produces a FILE_SET of the split audio files.

## Node: media.split_audio

**Type Name**: media.split_audio
**Cache Policy**: NEVER (Generates files dynamically into the workflow workspace).

### Inputs
- udio (DataType.FILE): The source audio artifact to be split.

### Config
- parts (int): Number of parts to divide the audio into. Minimum 2.
- ormat (str, optional): Target format (e.g. mp3, m4a). Defaults to the original file's extension if not provided.

### Outputs
- pieces (DataType.FILE_SET): A set containing the resulting split pieces.

## Behavior Rules

1. **Validation**: Check if the input file exists and is a valid audio format. Ensure parts >= 2.
2. **Duration Calculation**: The node will need to extract the total media duration. We'll add a helper get_media_duration utilizing fprobe to ktools_media.audio.extract or a new module ktools_media.media_info.
3. **Splitting Loop**:
   - Determine part_duration = total_duration / parts.
   - Iteratively execute fmpeg -ss {start} -t {duration} -i {input} {output}.
   - For the final piece, we can omit -t to ensure the audio extracts till the very end, avoiding slight duration miscalculations.
4. **Subprocess Tracking**: All fmpeg and fprobe calls must use ecord_subprocess for observability.
5. **Atomic Writes**: Each piece must be written to .tmp first, then atomically replaced to ensure execution interruptions do not leave corrupted files.

## Hand-off Checklist

- [ ] Create ktools_media.media_info with get_media_duration.
- [ ] Add split_audio capability to ktools_media.audio.split.
- [ ] Define the media.split_audio node contract.
- [ ] Write behavior unit tests (	est_media_split_behavior.py).
- [ ] Write engine execution tests (	est_media_split_engine.py).
- [ ] Update ROADMAP.md and CURRENT.md to reflect Slice 11 progress.

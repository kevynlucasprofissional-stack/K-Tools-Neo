# Spec: Media Join Audios Node V1

## Context

We adapt the legacy join_audio_files feature. To support diverse formats, the audio must be normalized to WAV format before concatenation. The Node will consume a FILE_SET of inputs and produce a single AUDIO artifact.

## Node: media.join_audios

**Type Name**: media.join_audios
**Cache Policy**: NEVER

### Inputs
- udios (DataType.FILE_SET): The source audio artifacts to be merged. The node expects udios to be a list of Artifact models inside the pieces or iles field of the workflow context (or however FILE_SET is passed). To be flexible, the inputs["audios"] could be the Artifact of type FILE_SET, and we would need to read the set. Wait, ktools_core passes inputs["audios"] as a single Artifact instance of type FILE_SET. But the node doesn't know the exact files!
Wait, in media.split_audio, I returned {"pieces": pieces_artifacts} where pieces_artifacts is list[Artifact]. ktools_core engine maps the return dict directly to the output ports! But wait, FILE_SET in ktools_core is just a DataType. If I returned a list[Artifact], the engine will pass a list[Artifact] to downstream nodes! So inputs["audios"] will be a list[Artifact].
Wait, let's verify how older.scan_files passes data. It outputs list[Artifact]. So inputs["audios"] will be list[Artifact].

### Config
- ormat (str): Target format (e.g. mp3, m4a, wav, lac). Default m4a.
- itrate (str, optional): The target bitrate.

### Outputs
- udio (DataType.AUDIO): The resulting merged audio artifact.

## Behavior Rules

1. **Validation**: Check if inputs["audios"] is a list of artifacts. If it's empty or has 1 item, we can still process it or error out. We'll enforce at least 2 items.
2. **Sorting**: Sort the artifacts by their uri or 
ame lexicographically to ensure stable and deterministic join order if they came from a directory scan.
3. **WAV Normalization**: Create a TemporaryDirectory. Iteratively execute fmpeg -y -i {input} {temp_wav} for every input.
4. **Concat List**: Create a concat.txt file inside the TemporaryDirectory formatted as ile 'part_001.wav'. Note: FFmpeg requires paths to be properly escaped or relative to the txt file.
5. **Merge**: Execute fmpeg -y -f concat -safe 0 -i concat.txt {final_args} {output_tmp}.
6. **Subprocess Tracking**: All fmpeg calls use ecord_subprocess.
7. **Atomic Writes**: The final piece must be written to .tmp first, then atomically replaced to ensure execution interruptions do not leave corrupted files.

## Hand-off Checklist

- [ ] Add join_audios capability to ktools_media.audio.join.
- [ ] Define the media.join_audios node contract.
- [ ] Write behavior unit tests (	est_media_join_behavior.py).
- [ ] Write engine execution tests (	est_media_join_engine.py).
- [ ] Update ROADMAP.md and CURRENT.md to reflect Slice 12 progress.

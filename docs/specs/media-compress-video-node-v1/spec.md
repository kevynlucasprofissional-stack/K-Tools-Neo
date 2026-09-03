# Spec: Media Compress Video Node V1

## Context

Video compression is a critical component for storage and bandwidth reduction. We will use FFmpeg's libx264 codec with a configurable crf (Constant Rate Factor).

## Node: media.compress_video

**Type Name**: media.compress_video
**Cache Policy**: NEVER

### Inputs
- ideo (DataType.FILE): The source video artifact.

### Config
- crf (int, default 28): H.264 compression factor (18-51 is typical, higher = smaller size).
- preset (str, default "medium"): H.264 preset (e.g., fast, medium, slow).

### Outputs
- ideo (DataType.VIDEO): The resulting compressed video artifact.

## Behavior Rules

1. **Validation**: Check if inputs["video"] is a valid artifact.
2. **Compression**: Execute fmpeg -y -i {input} -vcodec libx264 -crf {crf} -preset {preset} {output_tmp}.
3. **Subprocess Tracking**: All fmpeg calls use ecord_subprocess.
4. **Atomic Writes**: The final piece must be written to .tmp first, then atomically replaced.

## Hand-off Checklist

- [ ] Add compress_video capability to ktools_media.video.compress.
- [ ] Define the media.compress_video node contract.
- [ ] Write behavior unit tests (	est_media_compress_behavior.py).
- [ ] Write engine execution tests (	est_media_compress_engine.py).
- [ ] Update ROADMAP.md and CURRENT.md to reflect Slice 13 progress.

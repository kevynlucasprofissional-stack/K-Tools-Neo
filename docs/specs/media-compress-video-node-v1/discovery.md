# M5 Slice 13 Discovery: Media Compress Video Node V1

## Current State Analysis
Although Comprimir vídeo (Compress video) was marked as "future" in the legacy app's visual interface, it represents a core capability for any media orchestration pipeline to reduce artifact sizes. We will implement media.compress_video as our next node.

## Identified Capabilities
We will create media.compress_video in ktools_media.

- **Inputs**:
  - ideo (DataType.FILE): The source video artifact.
- **Config**:
  - crf (int, default 28): The Constant Rate Factor for H.264 compression. Lower is higher quality, higher is more compression.
  - preset (str, default "medium"): The x264 encoding preset.
- **Outputs**:
  - ideo (DataType.VIDEO): The compressed video artifact.

## Diagnostics/Observability Requirements
The node will invoke fmpeg with -vcodec libx264 -crf {crf} -preset {preset}.
Subprocesses must be tracked with ecord_subprocess. The output generation logic must adhere to atomicity (using .tmp writing).

## Next Steps
Proceeding to specification generation for Slice 13.

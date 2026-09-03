# M5 Slice 11 Discovery: Media Split Audio Node V1

## Current State Analysis
We have completed media.extract_audio and media.convert_audio. The legacy script K Tools Neo - Versão Estável 2.py includes an _audio_split_run capability that divides an audio file into N equal duration chunks. The split_audio_file underlying method accomplishes this by determining total duration, dividing it by N, and executing FFmpeg iteratively with -ss and -t for each chunk.

## Identified Capabilities
We will create media.split_audio which consumes a single DataType.FILE (audio source) and produces a DataType.FILE_SET containing the split artifacts.

- **Inputs**:
  - udio (DataType.FILE): Source audio file.
- **Config**:
  - parts (int): Number of equal parts (minimum 2).
  - ormat (str, optional): Target format for pieces (e.g. mp3, m4a). Defaults to the original extension.
- **Outputs**:
  - pieces (DataType.FILE_SET): A collection of the produced audio artifacts.

## Diagnostics/Observability Requirements
Like previous nodes, media.split_audio will execute fmpeg sequentially to produce each part. Every subprocess must be captured via ecord_subprocess. The output generation logic must adhere to atomicity (using .tmp writing).

## Next Steps
Proceeding to specification generation for Slice 11.

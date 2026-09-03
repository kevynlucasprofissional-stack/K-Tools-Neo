# M5 Slice 12 Discovery: Media Join Audios Node V1

## Current State Analysis
The legacy join_audio_files capability combines multiple audio files of potentially disparate formats (mp3, wav, m4a, flac) into a single unified track. Because sample rates and codecs differ, direct concat often fails or introduces glitches. The legacy implementation solves this by first using FFmpeg to decode all inputs into temporary .wav files, writing an fconcat script, and finally combining them into the desired output format.

## Identified Capabilities
We will create media.join_audios.

- **Inputs**:
  - udios (DataType.FILE_SET): The collection of audio files to merge. The node will order them lexicographically by filename to ensure deterministic results, or rely on the FILE_SET internal ordering if we can. Since FILE_SET currently returns a list of artifacts, we will sort them by metadata.name or uri natively.
- **Config**:
  - ormat (str): Target format (e.g. mp3, m4a, wav).
  - itrate (str, optional): The target bitrate.
- **Outputs**:
  - udio (DataType.AUDIO): The single merged output artifact.

## Diagnostics/Observability Requirements
The node will perform many subprocess operations:
1. fmpeg to convert each input to wav.
2. fmpeg to concat all wavs into the final output.
Every subprocess must be captured via ecord_subprocess. The output generation logic must adhere to atomicity (using .tmp writing). The WAV temporary files should be tracked within a temporary directory and wiped upon completion.

## Next Steps
Proceeding to specification generation for Slice 12.

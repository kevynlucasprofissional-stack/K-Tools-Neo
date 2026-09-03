# Discovery: Media Join Videos Node V1

## Context and Problem
The workspace contains JV.py ("Unificador de Vídeos Sequenciais") which uses moviepy to join videos. Furthermore, the legacy desktop monolith (K Tools Neo - Versão Estável 2.py) implements an FFmpeg-based join_video_files function using a two-tier strategy:
1. Fast concat with -c copy.
2. Fallback normalization using libx264/ac and concat demuxer.

Using pure FFmpeg (via ktools_media.ffmpeg.run_ffmpeg) instead of moviepy avoids heavy binary dependencies and ensures 100% compatibility with imageio-ffmpeg and the M3 DiagnosticsSession subprocess recorder.

## Candidate Node Definition
- Type: media.join_videos
- Inputs: ideos: FILE_SET (list of Video Artifacts)
- Outputs: ideo: VIDEO
- Config:
  - output_name (optional str, defaults to joined_video.mp4)
  - output_dir (optional str)
  - ast_copy (optional bool, defaults to True)

## Safety & Invariants
- Fail-closed if fewer than 2 video inputs provided.
- Preserves deterministic order based on filename / URI.
- Atomic publication via temporary .tmp intermediate file.
- Temporary files during fallback normalization are confined to a TemporaryDirectory and cleaned up.
- All FFmpeg executions monitored via un_ffmpeg and recorded in Diagnostics.

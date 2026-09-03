# ADR 032: Media Convert Audio Node V1

## Date
2026-09-02

## Status
Accepted

## Context
As part of M5 (Media Capabilities), we are migrating the legacy K-Tools media routines. The legacy tool offered a batch audio conversion interface for formats like MP3, M4A, WAV, FLAC. To fit into the DAG execution model, we need an atomic unit of audio conversion (media.convert_audio).

## Decision
- We created a media.convert_audio node.
- It expects an AUDIO or generic FILE artifact as input.
- It outputs an AUDIO artifact of the converted file.
- It writes the output file first to a .tmp file and then performs an atomic os.replace to ensure partial/aborted conversions don't pollute the target directory.
- It invokes un_ffmpeg without check=True but manually raises upon non-zero exit code to gracefully extract error output.
- Fixed a bug where _ACTIVE_SESSION leaked out of the Workflow Engine, making sequential test execution within the same python process cross-contaminate.

## Consequences
- Engine workflows can now transcode audio.
- The cache policy is NEVER because the node interacts with the underlying disk to construct the output file path.

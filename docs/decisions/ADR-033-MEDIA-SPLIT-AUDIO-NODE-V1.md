# ADR 033: Media Split Audio Node V1

## Date
2026-09-02

## Status
Accepted

## Context
As part of migrating legacy capabilities in M5, we needed a node to divide audio files into N equal segments. The legacy system ran a fmpeg loop with calculated -ss and -t slices. To integrate with the workflow engine, we need to encapsulate this logic in a node that consumes a FILE and produces a FILE_SET.

## Decision
- Developed media.split_audio that utilizes fprobe (via get_media_duration) to get the total duration.
- It iterates N times, building fmpeg commands that segment the track using -ss and -t.
- We use the DiagnosticsSession to track these subprocess invocations, accurately reflecting that 1 node may execute +1$ subprocesses.
- The output is formatted as a FILE_SET artifact containing child Artifact instances for each split track.

## Consequences
- We successfully represent 1-to-many outputs directly inside the Node engine's artifact graph representation.
- Downstream nodes can now theoretically fan-out over the FILE_SET.

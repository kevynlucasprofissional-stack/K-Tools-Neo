# Evidence — Media Extract Audio Node V1

Status: **SPEC GATE PENDING HOSTED CI**

## Prerequisite gate

M5 Slice 8 — Folder Scan Node V1 terminal documentation HEAD:
- HEAD `1a924dd...`;
- run `...`;
- Ubuntu / Windows / Python 3.10 / 3.13 / xyflow success.

## Fresh discovery evidence

Inspected the monolith and found remaining capabilities:
- Media/FFmpeg (audio join, audio split, audio cut, audio convert, audio extract, video join)
- PNG→ICO
- PDF compression

Media Extract Audio was selected over the others to establish the foundational `ktools_media` and safely integrate FFmpeg with M3 diagnostics before scaling up to broader A/V capabilities.

## Safety & diagnostic hypothesis

We assume that using `imageio-ffmpeg` guarantees FFmpeg availability cross-platform without system dependencies. We assume wrapping `subprocess.run` with `record_subprocess` will fulfill the M3 observability requirement for all FFmpeg calls.

## Spec gate

This docs-only commit must pass the unchanged hosted matrix before RED is authorized. No product implementation is changed by this spec gate.

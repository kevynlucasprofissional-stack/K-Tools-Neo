# ADR 035: Media Compress Video Node V1

## Date
2026-09-02

## Status
Accepted

## Context
Video artifacts are often large and cumbersome in data engineering pipelines. We required a method to decrease video footprint without losing essential visual information. The legacy implementation planned this but never finished it. 

## Decision
- We created the media.compress_video Node.
- It hardcodes the libx264 H.264 encoder as it offers the best combination of broad compatibility and size efficiency out of the box.
- It exposes crf and preset as simple node configurations, defaulting to standard 28 and "medium" respectively.
- Observability and atomicity strictly mirror the precedents set in M3.

## Consequences
- Videos can now be efficiently stored and managed.
- H.265/HEVC or hardware acceleration are left for future capability upgrades if required.

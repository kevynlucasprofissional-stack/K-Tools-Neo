# ADR 036: Media WebP to PNG Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The legacy K-Tools system included a batch WebP-to-PNG converter using Pillow. We need to migrate this as a reusable node capability.

## Decision
- Built media.webp_to_png node.
- Uses Pillow Image and ImageOps (imported at module level for testability).
- Handles first-frame extraction from animated WebPs.
- Uses EXIF-aware transpose to correct orientation.
- Converts to RGBA mode for full PNG transparency support.
- Atomic file writes via .tmp intermediate.

## Consequences
- WebP images from web scraping or design tools can now be normalised to PNG in workflows.
- Pillow is a runtime dependency for this node; it is already in the broader K-Tools dependency stack.

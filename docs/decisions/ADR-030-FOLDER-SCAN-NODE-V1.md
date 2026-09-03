# ADR-030 — Folder Scan Node V1

## Context
The legacy monolith contained overlapping file and folder traversal implementations. A reusable traversal source was needed for future features that compose file discovery with media, document, or image processing, without coupling traversal logic to the UI or presentation layer.

## Decision
- Extracted folder scanning into a standalone package `packages/ktools-filesystem`.
- Traversal logic now serves as the canonical implementation.
- Symlinks and reparse points are explicitly skipped to prevent traversal escapes from the base directory.
- `folder.scan_files` returns a structured `FILE_SET` and a JSON report accumulating nested read errors.
- The `folder.literal` and `folder.scan_files` nodes both enforce `CachePolicy.NEVER` as directory contents are volatile and tree snapshots are not currently strongly versioned.
- Output artifacts include semantic relative path metadata and are generated in a deterministic alphabetical order.

## Consequences
- Workflows can now begin with a target directory instead of a rigid list of explicitly passed file artifacts.
- The UI layer will no longer handle `os.walk` or filter extensions; it will simply call the API or spawn a workflow starting with `folder.literal`.
- Security against directory escape via symlinks is improved and tested.
- M5 Slice 8 is effectively finalized.

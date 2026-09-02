# ktools-documents

Official K-Tools Neo mixed-document orchestration Node Pack.

V1 owns the batch boundary for splitting ordered Markdown/TXT/PDF inputs while delegating all primitive transformation behavior to the canonical Text and PDF Node Packs.

Workflow node:

- `document.split.files: FILE_SET -> FILE_SET + JSON`, version 1, `CachePolicy.NEVER`.

The `files` output contains successful child Artifacts in input order then part order. The `report` output preserves batch counts, destination and per-source errors so partial success remains product-visible state.

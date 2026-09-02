# ktools-text

Official K-Tools Neo Text Node Pack.

V1 owns the canonical Markdown/TXT merge and balanced split behaviors behind shared direct-API/workflow implementation owners.

Current workflow nodes:

- `text.merge.files: FILE_SET -> FILE` — ordered Markdown/TXT merge, `CachePolicy.NEVER`;
- `text.split.parts: FILE -> FILE_SET` — balanced line-unit split with UTF-8 publication, `CachePolicy.NEVER`.

Built-in `file.literal` / `files.literal` remain the canonical local-file source nodes supplied by `ktools-core`.

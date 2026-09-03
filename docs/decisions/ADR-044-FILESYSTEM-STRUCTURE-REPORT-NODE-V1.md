# ADR 044: Filesystem Structure Report Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `EC.py` ("Extrator Completo de Estrutura de Pastas"), used to audit directory structures and generate reports. In data migrations, volume indexing, and project archiving, having tabular CSV inventories, formatted ASCII trees, and JSON metrics is essential.

## Decision
- Implement `filesystem.structure_report` node in `ktools-filesystem`.
- Takes a `FOLDER` artifact.
- Emits three synchronized outputs:
  - `csv`: comprehensive tabular list of every file/directory with relative paths, depths, sizes, and extensions.
  - `txt`: ASCII hierarchical tree view (`├──`, `└──`).
  - `json`: metrics payload with total files, total dirs, bytes, and extension counts.
- Gracefully handles self-referential `output_dir` nested within the target root.
- Atomic file publication via `.tmp` promotion.

## Consequences
- Deep storage analytics and audits can be performed cleanly in workflows without manual terminal scripts.

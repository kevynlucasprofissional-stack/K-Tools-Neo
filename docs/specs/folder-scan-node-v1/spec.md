# Spec — Folder Scan Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 Slice 8
Canonical implementation target: `packages/ktools-filesystem/`
Starting terminal main: `85985dd2abf9c6251a15332040e44a00def6798f`

## Objective

Extract one bounded, composable filesystem capability from the overlapping legacy Files/Folders scanners: enumerate regular local files under one local folder with explicit recursion, hidden-item, extension, symlink/reparse, ordering and error semantics.

The capability must expose the same scan owner through direct API and workflow execution, return first-class FILE Artifacts plus a structured JSON report, and remain independent from report-file exporters and GUI auto-trigger behavior.

## Fresh candidate decision

Slice 8 fresh discovery compared at minimum:

- bounded Files/Folders operations;
- PNG→ICO;
- PDF compression;
- the smallest useful Media/FFmpeg slice.

Folder Scan V1 is selected.

Reasons:

1. The legacy monolith has multiple overlapping traversal owners (`scan_folder_structure`, `scan_simple_file_names`, Markdown scanning, audio/video folder scans and helper scans), so canonicalization removes real transverse duplicate ownership rather than merely adding a new utility.
2. A folder source composes directly with existing Text, PDF, Documents, Images and future Media nodes.
3. It is the platform boundary needed for the product request “select a folder and discover the files automatically” while keeping traversal logic out of the future UI.
4. The V1 scan can be implemented with Python stdlib and no native/runtime dependency.
5. PNG→ICO is useful but currently a new isolated feature with less composition/duplicate-owner value.
6. PDF compression has no already-characterized canonical legacy algorithm and needs a separate quality/size semantic contract.
7. Media has high value but must first establish a shared FFmpeg/FFprobe native process boundary with M3 diagnostics, making it materially riskier than this filesystem slice.

## Scope boundary

This slice owns **file discovery only**.

It does not own:

- TXT/JSON/CSV/XLSX report publication;
- folder-tree text rendering;
- directory collection output;
- GUI callbacks or “scan on selection” behavior;
- filesystem watching;
- copy/move/delete/rename/mutation;
- generic filesystem framework design.

Legacy report/export paths remain characterization/compatibility sources, not implementation owners for V1 scanning.

## Package boundary

Create official package:

```text
packages/ktools-filesystem/
```

Runtime dependencies:

```text
ktools-core
Python standard library only
```

Python baseline remains >=3.10.

## Folder source contract

Add a minimal built-in source node in `ktools-core`:

```text
folder.literal: -> FOLDER
```

Version `1`, `CachePolicy.NEVER` in V1.

Config:

```json
{"path": "<local folder path>"}
```

It validates that the configured local path currently exists and is a directory and returns one `DataType.FOLDER` Artifact with a local `file://` URI and bounded metadata such as folder name.

Why NEVER: M4 explicitly has no strong folder-content validity contract. A cached path-only folder source could otherwise appear to imply reusable folder state. Folder-tree semantic identity is deferred.

The scan capability independently enforces its stricter root symlink/reparse rule.

## Production node contract

Node type:

```text
folder.scan_files
```

Version `1`.

Ports:

```text
folder: FOLDER -> files: FILE_SET
               -> report: JSON
```

Cache policy:

```text
NEVER
```

The scan is observational and has no publication side effect, but equivalent folder path/config does **not** yet imply equivalent folder contents. M4 semantic identity has strong local-file content validation, not a recursive folder-tree snapshot. Until that exists, caching this scan would risk stale discovery.

## Canonical capability owner

One business-logic owner, for example:

```python
ktools_filesystem.scanner.scan_files(
    root_folder,
    *,
    recursive=True,
    include_hidden=False,
    extensions=None,
    progress_callback=None,
    produced_by=None,
) -> FolderScanResult
```

Exact naming may vary during audit, but ownership may not.

`FolderScanResult` may be a small immutable/domain result carrying:

- ordered `files` tuple/list of FILE Artifacts;
- JSON-safe `report` mapping.

Direct API target:

```python
ktools_filesystem.api.scan_folder_files(...)
```

The API and workflow handler are thin adapters and must not duplicate traversal, filtering, sorting, hidden, reparse or error-aggregation algorithms.

## Root validity

The scan root must:

- be a local filesystem path or local FOLDER Artifact;
- currently exist;
- be a directory;
- not itself be a symlink or reparse point.

Root validation failure is fatal and raises a bounded public error such as `FolderScanError`.

Remote/UNC semantics are not expanded in this slice beyond the existing core local-file/local-URI policy.

## Traversal policy

V1 must not follow symlinks or filesystem reparse points.

Implementation may use `os.scandir` recursively or an equivalent stdlib traversal only if it preserves the same policy.

For each candidate entry:

- use non-following metadata (`lstat` / `follow_symlinks=False` semantics);
- skip symbolic links;
- on Windows, also skip entries with `FILE_ATTRIBUTE_REPARSE_POINT` where available;
- never recurse into a skipped link/reparse directory;
- never return a skipped link/reparse file as an ordinary FILE Artifact.

This is a safety boundary, not merely an optimization: a selected root must not silently escape into linked/junctioned trees.

## Recursion

Config:

```text
recursive: bool = true
```

- `true`: discover regular files at any traversed depth beneath the root, subject to all filters.
- `false`: inspect only direct children of the root; directories are not traversed.

Directories are never returned in V1.

## Hidden policy

Config:

```text
include_hidden: bool = false
```

Legacy-compatible V1 definition: an item is hidden when **any relative path component beneath the selected root begins with `.`**.

Examples when hidden files are excluded:

```text
.hidden.txt           -> hidden
.hidden/file.txt      -> hidden
normal/.cache/x.bin   -> hidden
normal/file.txt       -> visible
```

Windows hidden-file attributes are intentionally **not** added to V1 semantics. They require a separate product decision/evidence because the legacy cross-system helper is dot-component based.

When a hidden directory is excluded, traversal prunes that subtree.

## Extension filtering

Config:

```text
extensions: optional ordered/list-like collection of suffix strings
```

Rules:

- omitted / null / empty => include every otherwise-valid regular file;
- matching is case-insensitive;
- a missing leading `.` is normalized;
- duplicate normalized values collapse;
- invalid values containing path separators, wildcard characters or empty/dot-only tokens fail as configuration errors;
- filtering uses filename suffix matching; V1 is not a glob engine.

The normalized extension set/list is recorded in the report.

## Deterministic ordering

Traversal enumeration order from the OS is not product order.

After discovery, emitted files are globally sorted by their root-relative POSIX-style path using a deterministic key equivalent to:

```python
(relative_path.casefold(), relative_path)
```

This makes order stable across filesystems whose native directory enumeration order differs while retaining deterministic tie-breaking for case variants.

`sourceIndex` metadata follows this final order.

## Error boundary

Root validation or inability to enumerate the root itself is fatal.

For nested traversal/metadata failures (`PermissionError`/`OSError`), V1 is best-effort:

- record one structured error entry;
- skip the affected entry/subtree;
- continue scanning independent siblings where possible.

Error records are JSON-safe and bounded. They contain explicit fields such as:

```json
{
  "operation": "scandir",
  "relativePath": "locked",
  "errno": 13,
  "message": "Permission denied"
}
```

Do not serialize arbitrary `repr()` values or opaque objects.

A successful scan may therefore return files plus non-zero `errorCount`.

An empty successful FILE_SET is valid when the root is valid but no file matches.

## Artifact contract

Each emitted member is a `DataType.FILE` Artifact:

- local `file://` URI;
- current `produced_by` when supplied by direct/workflow caller;
- metadata includes at minimum:
  - `name`;
  - `relativePath` using `/` separators;
  - `extension` (case-normalized final suffix or empty string);
  - `sourceIndex` in final deterministic order;
  - `sizeBytes` when metadata was successfully obtained.

Workflow execution must allow ArtifactRegistry to record strong local-file snapshots for every emitted FILE Artifact.

Do not invent a `FOLDER_SET` or specialized file collection for this slice.

## Report contract

The JSON report includes at minimum:

- root URI/path representation suitable for local product use;
- `recursive`;
- `includeHidden`;
- normalized `extensions`;
- `fileCount`;
- `errorCount`;
- `errors`;
- `skippedHidden` count;
- `skippedReparse` count;
- `ordering = "relative-path-casefold"` or equivalent stable versioned statement;
- `reparsePolicy = "skip-no-follow"` or equivalent;
- `hiddenPolicy = "dot-relative-component"` or equivalent.

The report is product state, not merely diagnostics. It must be returned even when nested non-fatal errors occur.

## Progress contract

Progress is supplemental and must remain within `[0.0, 1.0]`.

Because total tree size is not known before traversal, V1 does not claim exact percentage-by-files semantics during discovery. A callback may emit bounded monotonic phase/observation progress and final `1.0` only after sorting/report construction completes.

Do not perform a second full traversal merely to calculate an exact denominator.

## Composition contract

The primary hosted proof must execute:

```text
folder.literal -> folder.scan_files
```

A stronger composition smoke should, where deterministic and inexpensive, feed scanned `.txt` files into the existing Text merge node:

```text
folder.literal -> folder.scan_files -> text.merge.files
```

This proves the filesystem source produces a real ordered FILE_SET reusable by an existing canonical capability.

## Required RED

The docs-only spec HEAD must first pass all five current hosted jobs.

Then add discriminating tests that:

- leave all pre-existing Core/JSON/Text/PDF/Documents/Images suites available;
- fail because `folder.literal` and/or the `ktools_filesystem` scan contracts are absent;
- do not fail because of a new dependency/bootstrap mistake.

The expected RED boundary is missing product contract, not environment failure.

## Required tests

At minimum prove:

1. `folder.literal` exists, returns FOLDER, version 1, NEVER, and rejects missing/non-directory paths;
2. valid root with zero files succeeds with empty FILE_SET/report count zero;
3. recursive true vs false behavior;
4. dot-component hidden pruning and include-hidden override;
5. extension normalization, case-insensitive matching, duplicate normalization and invalid-config rejection;
6. deterministic global relative-path ordering independent of mocked/enumerated discovery order;
7. regular file Artifact type/URI/metadata/sourceIndex;
8. root symlink/reparse rejection;
9. nested symlink/reparse file/directory skipping without traversal;
10. nested `PermissionError`/`OSError` accumulation with sibling continuation;
11. root enumeration failure is fatal;
12. `folder.scan_files: FOLDER -> FILE_SET + JSON`, version 1, NEVER;
13. direct API and workflow produce semantically equivalent ordered paths/report in isolated executions;
14. node/API contain no traversal/filter/sort/reparse algorithms;
15. ArtifactRegistry strongly snapshots emitted nested FILE_SET members;
16. repeated workflow execution after adding/removing a file sees current folder state and scan is never NODE_CACHED;
17. no filesystem mutation/publication occurs;
18. existing source/file/cardinality/cache/runtime regressions remain green.

## Hosted CI

GREEN must update root CI so every Python lane:

- installs `ktools-filesystem` after `ktools-core`;
- runs the filesystem package suite;
- executes real `folder.literal -> folder.scan_files` smoke;
- preferably executes scan→Text merge composition using deterministic generated `.txt` files;
- verifies ordered file names/content and JSON report semantics.

Matrix remains Ubuntu/Windows × Python 3.10/3.13 plus xyflow.

## Non-goals

- report files (TXT/JSON/CSV/XLSX);
- directory output collection/tree rendering;
- automatic GUI trigger;
- filesystem watcher;
- recursive folder-content cache/signature;
- Windows hidden-attribute expansion;
- following symlinks, junctions or reparse points;
- copy/move/delete/rename;
- permission repair;
- glob/regex query language;
- generic filesystem abstraction framework;
- media/FFmpeg work;
- PNG→ICO or PDF compression.

## Promotion rule

```text
terminal Slice-7 main
  -> fresh Slice-8 discovery
  -> docs-only Folder Scan spec gate
  -> discriminating RED
  -> GREEN implementation
  -> integration/security/ownership audit
  -> exact-head hosted 5/5
  -> ADR + canonical memory closure
  -> terminal closure HEAD CI 5/5
```

No promotion claim before the synchronized closure HEAD itself is green.

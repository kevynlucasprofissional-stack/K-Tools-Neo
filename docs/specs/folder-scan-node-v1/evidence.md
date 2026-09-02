# Evidence — Folder Scan Node V1

Status: **SPEC GATE PENDING HOSTED CI**

## Prerequisite gate

M5 Slice 7 — Images→PDF Node V1 terminal documentation HEAD:

- HEAD `85985dd2abf9c6251a15332040e44a00def6798f`;
- run `33675089416`;
- Ubuntu / Python 3.10 success;
- Ubuntu / Python 3.13 success;
- Windows / Python 3.10 success;
- Windows / Python 3.13 success;
- xyflow success.

Every Python lane reached all installed-pack suites and hosted smokes including Images→PDF. Slice 8 therefore begins from a terminal-green mainline.

## Fresh discovery evidence

The legacy monolith was inspected before selection.

Observed overlapping traversal ownership includes at least:

- `scan_folder_structure(...)`;
- `scan_simple_file_names(...)`;
- Markdown folder scanning;
- audio folder scanning;
- video folder scanning;
- additional scan helpers.

The Files/Folders UI historically combines traversal with structure/list/names/summary modes, files/dirs/hidden/subfolder controls and TXT/JSON/CSV/XLSX export concerns. V1 deliberately separates the reusable traversal source from those presentation/publication surfaces.

Legacy semantics also exposed useful characterization facts:

- `os.walk`-style traversal and error accumulation exist;
- hidden-like policy is based on relative path components starting with `.`;
- subfolder inclusion is configurable;
- different features currently implement their own folder enumeration.

## Candidate comparison

### Folder Scan

Strengths: high composition value, no new dependency, direct product request alignment, multiple duplicate legacy owners, unlocks future UI auto-scan while keeping runtime ownership outside UI.

Risk: cross-platform symlink/reparse and ordering/error semantics needed explicit locking. This spec locks them.

### PNG→ICO

Useful explicit backlog item, but primarily a new isolated image conversion with less immediate composition/duplicate-owner reduction than filesystem discovery.

### PDF compression

Explicit backlog item, but no already-characterized canonical legacy compressor was found during discovery. Quality/size/serializer semantics require their own dedicated spec rather than being inferred.

### Media / FFmpeg

High product value and legacy FFmpeg usage exists, but the first canonical Media slice must establish one native FFmpeg/FFprobe execution boundary integrated with M3 diagnostics and M4 Artifact/cache rules. That is a larger risk surface than bounded stdlib file discovery.

## Selected hypothesis

A single no-follow deterministic scanner can become the canonical file-discovery owner while report exporters and GUI triggers stay outside the slice.

The expected architecture is:

```text
folder.literal -> FOLDER
                    ↓
             folder.scan_files (NEVER)
               ↙             ↘
          FILE_SET          JSON report
```

## Cache hypothesis

Both folder source and scan are specified NEVER for V1.

Reason: current strong reusable validity is defined for local files, not recursive folder-tree contents. A path-identical folder can change between runs. RED/GREEN must eventually prove a second identical workflow execution sees newly added/removed files instead of substituting stale results.

## Safety hypothesis

Root symlinks/reparse points are rejected and nested symlink/reparse entries are skipped without following them. This avoids traversal escaping the selected root through Unix symlinks or Windows junction/reparse constructs.

## Spec gate

This docs-only commit must pass the unchanged five-job hosted matrix before RED is authorized.

No product implementation or CI surface is changed by this spec gate except the correction of the stale branch-only sentence in `docs/CONSTRAINTS.md` to match the already-active Solo/Main-Only policy.

## Next accepted evidence

1. exact spec HEAD hosted 5/5;
2. discriminating RED that reaches absent `folder.literal` / `ktools_filesystem` product contracts after prior suites remain healthy.

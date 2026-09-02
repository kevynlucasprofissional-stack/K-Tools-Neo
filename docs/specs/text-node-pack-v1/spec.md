# Spec — Text Node Pack V1

Status: **ACTIVE / RED**
Milestone: M5 — first local Node Pack slice
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Migrate the existing Markdown/TXT merge behavior out of the legacy CustomTkinter monolith into a reusable Text Node Pack without duplicating business logic and without weakening M0-M4 contracts.

The real legacy owner is `merge_text_files(...)` in `K Tools Neo - Versão Estável 2.py`.

## Candidate decision

Markdown/TXT merge is selected before WebP→PNG and generic folder scanning because it is a bounded stdlib-only behavior with low native coupling. WebP→PNG brings Pillow/image-safety/EXIF/alpha/animation semantics; generic folder scan is still UI/callback coupled.

## Characterized legacy contract

Supported behavior establishes:

- ordered `.md` / `.txt` inputs;
- empty/missing/non-file/unsupported inputs rejected;
- decoding order `utf-8-sig` → `utf-8` → `latin-1`;
- non-text output suffix normalized to `.md`;
- output cannot be one of the inputs;
- destination parent is created;
- same-directory temporary output precedes final `os.replace`;
- an existing non-input destination is replaced on success;
- failure before replacement preserves the previous destination and cleans temp output where possible;
- `completo` adds legacy start/end provenance markers;
- `simples` adds `# filename` headings;
- `nenhum` adds no heading/marker;
- every non-`completo` input is followed by two newline characters;
- input order is semantic.

## Package boundary

`packages/ktools-text/` owns formatting, decoding/publication orchestration, direct API and thin node adapter.

One-owner flow:

```text
render_merged_text
       ↓
writer.merge_text_files
   ↙             ↘
direct API    text.merge.files
```

## FILE_SET contract

Add `DataType.FILE_SET = "file_set"`.

A FILE_SET runtime value is an ordered list/tuple of Artifact values. V1 compatibility is exact FILE_SET→FILE_SET. No collection class is needed because M4 signature/cache/Artifact traversal already handles list/tuple recursively.

A minimal built-in `files.literal` source is added to make file-set workflows composable before the production UI exists. It accepts configured local paths, validates them, preserves order and emits FILE_SET Artifacts. It is PURE because it has no publication side effect; M4 cached-output Artifact validation prevents stale/missing file references from being reused silently.

## Main node

`text.merge.files`

- input `files: FILE_SET`;
- output `file: FILE`;
- config `output_path` and `separator_mode` (`completo` default, `simples`, `nenhum`);
- version `1`;
- cache policy `NEVER` because publishing/replacing a requested filesystem result is required behavior.

The output is a first-class FILE Artifact with current `run_id/node_id` provenance.

## Acceptance

### A — FILE_SET + source
- [ ] enum/type contract exists;
- [ ] FILE_SET edges validate exactly;
- [ ] FILE and FILE_SET are not interchangeable;
- [ ] `files.literal` preserves configured order and returns Artifacts;
- [ ] missing/empty paths fail;
- [ ] M4 can cache `files.literal` only while output files remain valid.

### B — legacy merge bytes
- [ ] UTF-8 BOM, UTF-8 and latin-1 decoding behavior preserved;
- [ ] complete/simple/none bytes match characterized legacy behavior;
- [ ] input order preserved;
- [ ] suffix normalization preserved.

### C — publication safety
- [ ] output/input collision rejected;
- [ ] parent creation;
- [ ] existing destination replaced only after successful temp write;
- [ ] mid-operation failure preserves previous destination;
- [ ] handled failure cleans temp output where possible.

### D — one-owner architecture
- [ ] direct API and node reach shared writer owner;
- [ ] node does not duplicate merge logic;
- [ ] direct/node equivalent runs are byte-identical.

### E — M4 integration
- [ ] output Artifact carries current run/node provenance;
- [ ] ArtifactRegistry records EXECUTED occurrence + strong snapshot;
- [ ] merge node NEVER executes again on equivalent repeated run;
- [ ] upstream `files.literal` may be CACHED independently.

### F — hosted regression
- [ ] root CI installs/tests ktools-text;
- [ ] Windows/Linux Python 3.10/3.13 green;
- [ ] core/JSON regressions green;
- [ ] text workflow smoke proves a real merged file;
- [ ] xyflow remains green.

## Non-goals

Broad Text toolbox, images/PDF/media, folder-scan UX, FFmpeg, dynamic plugins, production editor, side-effect cache replay and full legacy GUI replacement are outside this slice.

## Promotion rule

A second independent canonical merge implementation may not remain indefinitely. After package equivalence is proved, legacy ownership must be redirected/deprecated/documented explicitly before this slice is considered fully migrated.

# Spec — Text Node Pack V1

Status: **IMPLEMENTATION COMPLETE / CANONICAL MEMORY CI PENDING**
Milestone: M5 — Official local Node Packs, Slice 1
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Migrate the existing Markdown/TXT merge behavior out of the legacy CustomTkinter monolith into a reusable Text Node Pack without duplicating business logic and without weakening M0-M4 contracts.

The legacy `merge_text_files(...)` in `K Tools Neo - Versão Estável 2.py` is the **characterization source** for supported historical behavior. After this slice, it is not the canonical evolution owner.

## Candidate decision

Markdown/TXT merge was selected before WebP→PNG and generic folder scanning because it is a bounded stdlib-only behavior with low native coupling. WebP→PNG brings Pillow/image-safety/EXIF/alpha/animation semantics; generic folder scan is still UI/callback coupled.

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

`packages/ktools-text/` owns formatting, decoding/publication orchestration, direct API and the thin workflow adapter.

One-owner flow:

```text
render_document_block
        ↓
writer.merge_text_files
   ↙                 ↘
direct API        text.merge.files
```

`render_merged_text` remains a deterministic convenience/characterization surface; the writer deliberately streams one document block at a time so large files are not unnecessarily accumulated in memory.

## FILE_SET contract

M5 introduces `DataType.FILE_SET = "file_set"`.

A FILE_SET runtime value is an ordered list/tuple of Artifact values. V1 compatibility is exact FILE_SET→FILE_SET. No collection class is needed because M4 signature/cache/Artifact traversal already handles list/tuple recursively.

A minimal built-in `files.literal` source makes file-set workflows composable before the production UI exists. It accepts configured local paths, validates them, preserves order and emits FILE Artifacts through a FILE_SET port. It is `PURE` because it has no publication side effect; M4 cached-output Artifact validation prevents stale/missing file references from being reused silently.

## Main node

`text.merge.files`

- input `files: FILE_SET`;
- output `file: FILE`;
- config `output_path` and `separator_mode` (`completo` default, `simples`, `nenhum`);
- version `1`;
- cache policy `NEVER` because publishing/replacing a requested filesystem result is required behavior.

The output is a first-class FILE Artifact with current `run_id/node_id` provenance.

## Shared local-file boundary

Integration review found that M4 cache identity and the Text adapter had independently implemented `file:// URI → Path` conversion. The duplicate was removed before promotion.

`ktools_core.local_files.path_from_file_uri()` is now the single cross-platform parser for supported local file URIs. M4 translates its generic error into `UnsupportedArtifactError`; Text translates it into `TextMergeError`.

## Ownership after promotion

Canonical owner for Markdown/TXT merge behavior:

`packages/ktools-text/src/ktools_text/`

The old stable GUI still contains and invokes a historical copy until a later UI-adapter migration. That copy is **compatibility debt, not a second canonical owner**. New behavior, fixes and contract changes must originate in `ktools-text`; the old GUI path must later delegate to the package or be retired. This boundary is tracked in `KNOWN_ISSUES.md`.

## Acceptance

### A — FILE_SET + source
- [x] enum/type contract exists;
- [x] FILE_SET edges validate exactly;
- [x] FILE and FILE_SET are not interchangeable;
- [x] `files.literal` preserves configured order and returns Artifacts;
- [x] missing/empty paths fail;
- [x] M4 can cache `files.literal` only while output files remain valid.

### B — legacy merge bytes
- [x] UTF-8 BOM, UTF-8 and latin-1 decoding behavior preserved;
- [x] complete/simple/none bytes match characterized legacy behavior;
- [x] input order preserved;
- [x] suffix normalization preserved.

### C — publication safety
- [x] output/input collision rejected;
- [x] parent creation;
- [x] existing destination replaced only after successful temp write;
- [x] mid-operation failure preserves previous destination;
- [x] handled failure cleans temp output where possible.

### D — one-owner architecture
- [x] direct API and node reach shared writer owner;
- [x] node does not duplicate merge logic;
- [x] direct/node equivalent runs are byte-identical;
- [x] local-file URI resolution is shared with core rather than duplicated.

### E — M4 integration
- [x] output Artifact carries current run/node provenance;
- [x] ArtifactRegistry records EXECUTED occurrence + strong snapshot;
- [x] merge node `NEVER` executes again on equivalent repeated run;
- [x] upstream `files.literal` may be CACHED independently;
- [x] source-file mutation invalidates the cached FILE_SET candidate.

### F — hosted regression
- [x] root CI installs/tests ktools-text;
- [x] Windows/Linux Python 3.10/3.13 green on accepted code candidate;
- [x] core/JSON regressions green;
- [x] text workflow smoke proves a real merged file;
- [x] xyflow remains green;
- [ ] final canonical-memory HEAD passes the same matrix before merge.

## Accepted code candidate

HEAD: `dbd39a1119ce1557d802a115404f01a3f797d93e`

Hosted run: `33627879876`

Result: five of five jobs succeeded.

## Non-goals

Broad Text toolbox, images/PDF/media, folder-scan UX, FFmpeg, dynamic plugins, production editor, side-effect cache replay and full legacy GUI replacement are outside this slice.

## Promotion rule

The slice may be promoted after canonical memory is synchronized and that exact documentation HEAD passes the full hosted matrix. The historical GUI copy may remain temporarily only as explicitly tracked compatibility debt; it must not be treated as a valid place to evolve merge semantics.

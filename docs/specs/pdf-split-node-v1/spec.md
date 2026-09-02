# Spec — PDF Split Node V1

Status: **RESOLVED / PROMOTED**
Milestone: M5 — Official local Node Packs, Slice 3
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Extend canonical `packages/ktools-pdf/` with the legacy balanced PDF split capability and prove one local PDF can become an ordered set of safely published PDF Artifacts through one shared direct-API/workflow implementation owner.

Historical characterization source: `split_pdf_into_parts(...)` in `K Tools Neo - Versão Estável 2.py`.

## Selected architecture

Fresh discovery compared PDF split, Images→PDF, WebP→PNG, mixed Document Split and bounded Files/Folders scan. PDF split was selected because it reuses the accepted `pypdf`/checked-reader/atomic-publication boundary, adds a real one-file→multi-file contract, and removes a prerequisite for later Document Split migration.

Canonical path:

```text
checked reader + balanced planner + atomic PDF publisher
                      ↓
          splitter.split_pdf_into_parts
             ↙                    ↘
        direct API             pdf.split.parts
```

`node.py` remains an adapter; it does not own page partitioning, page-copy loops, collision naming or PDF publication.

## Contracts

### `file.literal`

- config: `path` local file path;
- output: `file: FILE`;
- version: `1`;
- cache: `PURE`;
- shares local Artifact construction/validation with `files.literal`;
- M4 strong local-file revalidation invalidates stale cache after content mutation.

### `pdf.split.parts`

- input: `file: FILE`;
- output: `files: FILE_SET` whose members are PDF Artifacts;
- config: `output_dir`, integer `parts >= 2`; bool is rejected;
- version: `1`;
- cache: `NEVER` because publication is required behavior.

No `PDF_SET` is introduced. `FILE_SET` is sufficient because members preserve `Artifact.type == PDF`, ArtifactRegistry snapshots nested members, and `pdf.split.parts -> pdf.merge.files` composes directly.

## Preserved behavior

- one local `.pdf` input;
- missing/directory/non-PDF input rejected;
- protected/encrypted/corrupt/zero-readable-page PDF fails closed;
- requested parts clamp to page count;
- balanced contiguous ranges, e.g. 5 pages / 3 parts = 2/2/1;
- `{stem}_parte_XX_de_YY.pdf` naming using actual clamped part count;
- existing/reserved names never overwritten; `_1`, `_2`, ... suffixes are selected;
- each part is atomically published;
- output order follows page order;
- supplemental progress reaches completion without owning semantics;
- failure is not all-or-nothing across the set: earlier successfully published parts may remain if a later part fails, while the failing destination is not left partial or falsely claimed.

## Artifact semantics

Each output member is:

- `Artifact.type == PDF`;
- MIME `application/pdf`;
- local normalized `file://` URI;
- workflow provenance `{run_id}/{node_id}`;
- JSON-safe metadata including part index/count and page range/count.

## Acceptance — satisfied

### A — characterization

- [x] missing/directory/non-PDF source rejected;
- [x] invalid `parts` rejected;
- [x] requested parts clamp to page count;
- [x] balanced contiguous partitioning characterized;
- [x] deterministic clean-folder naming characterized;
- [x] collision-safe suffix naming characterized;
- [x] empty/encrypted/corrupt PDF fails closed;
- [x] progress reaches completion without owning semantics.

### B — source/platform

- [x] `file.literal: -> FILE`, version 1, PURE;
- [x] single/multi file literals share local Artifact owner;
- [x] strong cache invalidation after file mutation.

### C — one owner

- [x] `splitter.split_pdf_into_parts` owns split behavior;
- [x] direct API delegates to splitter;
- [x] node adapter delegates to splitter;
- [x] checked reader + shared atomic writer reused;
- [x] structural guards prevent split algorithm duplication in adapter.

### D — workflow/Artifact

- [x] `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- [x] output members are PDF Artifacts with provenance/page metadata;
- [x] ArtifactRegistry snapshots nested outputs;
- [x] cached `file.literal` does not suppress split publication;
- [x] repeated split collision-safely publishes new files.

### E — equivalence/composition

- [x] direct API/workflow semantic equivalence;
- [x] split→merge recreates source page order/count semantics.

### F — hosted regression

- [x] Ubuntu Python 3.10/3.13;
- [x] Windows Python 3.10/3.13;
- [x] Core/JSON/Text regressions green;
- [x] hosted split→merge smoke reopens parts and recomposed PDF in every Python lane;
- [x] xyflow green.

## Evidence chain

- prerequisite Slice 2 closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5;
- Slice 3 spec gate `a09d600924aa66d031cc2bcc2f59feb04bdf0704`, run `33652921999`, 5/5;
- RED `e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`, previous suites green and new PDF split tests red at missing product contracts;
- GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925`, run `33653824159`, 5/5;
- hardened technical candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e`, run `33654265424`, 5/5 including hosted split→merge smoke.

## Non-goals preserved

Mixed document split, Images→PDF, WebP conversion, arbitrary page expressions, password decryption, PDF_SET, set-wide transactionality, production editor changes and broad stable-GUI rewrites remain outside this slice.

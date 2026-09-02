# Spec — PDF Split Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 — Official local Node Packs, Slice 3
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Extend the canonical `packages/ktools-pdf/` owner with the legacy PDF split capability and prove that one local PDF can be divided into an ordered set of safely published PDF Artifacts through the same direct-API/workflow implementation owner.

Historical characterization source: `split_pdf_into_parts(...)` in `K Tools Neo - Versão Estável 2.py`.

## Slice selection

Fresh discovery after PDF Merge V1 compared the remaining bounded owners:

| Candidate | Dependency boundary | New contract pressure | Legacy coupling | Slice-3 fit |
|---|---|---|---|---:|
| PDF split | existing `pypdf` | one-file input + multi-file output | already reused by Document Split | **selected** |
| Images→PDF | new Pillow policy | EXIF, alpha flattening, animation, decompression safety | standalone | later |
| WebP→PNG | new Pillow policy | image FILE_SET output, alpha/animation | standalone | later |
| Document split | mixed Text + PDF orchestration | cross-pack dispatch/error aggregation | already delegates to PDF split | after primitives |
| Files/Folders scan | stdlib | folder traversal + JSON/report semantics | broad feature surface | later bounded slice |

PDF split is selected because it reuses the accepted PDF dependency/reader/publication boundary, introduces a real cardinality/composition requirement, and removes a prerequisite for migrating mixed Document Split later.

## Legacy behavior to characterize

The legacy owner establishes:

- input is one local `.pdf` path;
- missing/non-file/non-PDF inputs fail;
- `parts` must be at least 2;
- the PDF is opened through the checked reader boundary;
- protected/encrypted/corrupt/no-readable-page inputs fail closed;
- requested parts are clamped to the page count;
- pages are divided into balanced contiguous ranges; earlier parts may contain one extra page;
- output folder is created when absent;
- output names use `{stem}_parte_{index:02d}_de_{actual_parts:02d}.pdf`;
- existing/reserved names are not overwritten: a numeric suffix is selected instead;
- each output PDF is published through the PDF writer's atomic temp-then-replace boundary;
- output order follows page-range order;
- progress callback is supplemental and owns no split semantics;
- the legacy function returns the ordered output paths.

V1 may normalize error wording, but not supported page partitioning, order, collision avoidance or publication semantics.

## Package boundary

Extend, do not create a second PDF package:

```text
packages/ktools-pdf/src/ktools_pdf/
  reader.py          # checked PDF read boundary
  writer.py          # shared atomic PDF publication + merge
  splitter.py        # PDF split planning/publication owner
  api.py             # thin direct API
  node.py            # thin workflow adapters
```

One-owner split path:

```text
checked reader + split planner + atomic PDF publisher
                      ↓
          splitter.split_pdf_into_parts
             ↙                    ↘
        direct API             pdf.split.parts
```

The node adapter must not contain page partitioning, page-copy loops, collision naming or publication logic.

## Minimal single-file source contract

Add builtin node:

`file.literal`

Config:

- `path`: required local file path string.

Output:

- `file: FILE`.

Version: `1`.
Cache policy: `PURE`.

`file.literal` and existing `files.literal` must share one local-file Artifact construction/validation helper. Do not duplicate path validation or Artifact metadata semantics.

M4 strong Artifact revalidation is the validity proof for cached file literals.

## PDF split node contract

Type id:

`pdf.split.parts`

Input:

- `file: FILE` — runtime-validated as a supported local PDF. `PDF` output Artifacts may feed this FILE input through existing subtype compatibility.

Output:

- `files: FILE_SET` — ordered list of output Artifacts. Each member is type `PDF`, MIME `application/pdf`.

Config:

- `output_dir`: required destination directory path/string;
- `parts`: required integer >= 2; boolean is not accepted as an integer configuration value.

Version: `1`.
Cache policy: `NEVER`.

Reason: publication of new part files is required behavior. A cached list of old Artifact references is not equivalent to performing the requested split, especially because collision-safe naming can intentionally produce new paths on repeated runs.

## FILE_SET decision

Do **not** add `PDF_SET` in V1.

This is the second real PDF collection use case, so the earlier deferral is explicitly revisited. `FILE_SET` remains sufficient because:

- every member retains first-class `Artifact.type == PDF`;
- ArtifactRegistry can snapshot nested PDF Artifacts;
- `pdf.split.parts -> pdf.merge.files` composes directly without collection-conversion nodes;
- a new collection type would add graph compatibility rules without increasing runtime truth for this use case.

Revisit typed collection specialization only if a future capability needs graph-time element-type rejection that runtime Artifact typing cannot represent safely.

## Artifact semantics

Every split output Artifact:

- type `PDF`;
- local normalized `file://` URI;
- `produced_by = {run_id}/{node_id}` for workflow execution;
- MIME `application/pdf`;
- JSON-safe metadata including `partIndex`, `partCount`, `pageStart`, `pageEnd`, `pageCount`, and source name where useful.

The ordered list itself is the FILE_SET value; no wrapper class is introduced.

## Collision and publication policy

Preserve legacy non-overwrite behavior:

- clean target name first;
- if it exists or was reserved in the same batch, choose `_1`, `_2`, ... before `.pdf`;
- never silently replace an existing part file;
- each selected path is written atomically;
- a handled failure must not leave a partial file at the failing destination;
- V1 does not claim all-or-nothing transactionality across the entire multi-file set; earlier successfully published parts may remain if a later part fails. This boundary must be explicit and tested where practical.

## Shared PDF writer refactor

`write_pdf_writer_atomic()` is reusable for merge and split, but its failure wording must be operation-neutral. Do not fork a second atomic PDF writer.

Do not generalize PDF-specific publication into `ktools-core` merely because Text/JSON/PDF all use temp files. A third cross-domain abstraction requires a stable shared contract, not visual similarity.

## Direct/workflow composition proof

The strongest V1 proof is:

```text
file.literal -> pdf.split.parts -> pdf.merge.files
```

On a deterministic fixture PDF, the recomposed PDF must preserve the source page count and ordered page markers/dimensions.

This proves:

- one-file source cardinality;
- FILE -> FILE_SET -> PDF typed composition;
- PDF Artifacts inside FILE_SET;
- split publication;
- merge consumption of split outputs;
- no need for PDF_SET.

## Acceptance

### A — characterization RED

- [ ] missing/directory/non-PDF source rejected;
- [ ] parts < 2, bool and non-integer config rejected;
- [ ] parts > page count clamps to page count;
- [ ] balanced contiguous partitioning characterized (e.g. 5 pages -> 3 parts = 2/2/1);
- [ ] deterministic clean-folder naming characterized;
- [ ] collision-safe suffix naming characterized;
- [ ] empty/encrypted/corrupt PDF fails closed;
- [ ] progress reaches completion without owning semantics.

### B — platform/source contract

- [ ] `file.literal: -> FILE`, version 1, PURE;
- [ ] `file.literal` and `files.literal` share local Artifact construction;
- [ ] file literal cache is strongly invalidated by source content mutation.

### C — package owner

- [ ] `splitter.split_pdf_into_parts` is the single split implementation owner;
- [ ] direct API delegates to splitter;
- [ ] node adapter delegates to splitter;
- [ ] split reuses checked reader and atomic PDF writer;
- [ ] structural guard prevents page partition/copy logic from moving into adapter.

### D — workflow/Artifact contract

- [ ] `pdf.split.parts` is FILE -> FILE_SET, version 1, NEVER;
- [ ] each output member is a PDF Artifact with provenance and page-range metadata;
- [ ] ArtifactRegistry records/snapshots nested split outputs;
- [ ] cached `file.literal` may be reused while split still executes;
- [ ] repeated split in same output directory publishes collision-safe new files rather than cache-skipping or overwriting.

### E — equivalence/composition

- [ ] direct API and workflow produce semantically equivalent page ranges in clean independent directories;
- [ ] split -> merge end-to-end composition recreates original page order/count semantics.

### F — hosted regression

- [ ] PDF suite passes Ubuntu/Windows Python 3.10/3.13;
- [ ] core/JSON/Text regressions remain green;
- [ ] hosted PDF split workflow smoke reopens every part and verifies page ranges;
- [ ] hosted split -> merge composition smoke passes at least one Python lane per OS (or all matrix lanes if inexpensive);
- [ ] xyflow remains green.

## Non-goals

- mixed MD/TXT/PDF document split in this slice;
- Images→PDF or WebP conversion;
- PDF extraction by arbitrary page expressions/ranges;
- per-page split mode distinct from balanced `parts` contract;
- password decryption/cracking;
- PDF_SET;
- all-or-nothing transaction across the whole output set;
- production visual editor changes;
- broad stable-GUI rewrite.

## Promotion rule

Promote only after spec gate, discriminating RED, GREEN, integration audit, exact-head Windows/Linux + xyflow hosted evidence, explicit canonical ownership/debt classification, terminal memory closure and green terminal `main` HEAD.

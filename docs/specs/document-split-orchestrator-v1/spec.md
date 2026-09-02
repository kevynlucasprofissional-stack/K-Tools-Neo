# Spec — Mixed Document Split Orchestrator V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 — Official local Node Packs, Slice 5
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Extract the historical mixed `.md` / `.txt` / `.pdf` batch split boundary as a thin orchestration Node Pack that delegates primitive work to the already-canonical Text and PDF splitters, preserves legacy batch continuation/progress/report semantics, and introduces no third split algorithm.

## Fresh Slice-5 selection

After Text Split V1 terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` passed hosted run `33661273251` 5/5, the remaining bounded candidates were re-inspected.

| Candidate | Dependency/security boundary | New contract pressure | Duplicate-owner reduction | Slice-5 fit |
|---|---|---|---|---:|
| Mixed Document Split | no new transformation dependency; depends on canonical Text/PDF packs | batch dispatch, partial success, report + FILE_SET | removes legacy orchestration owner now that both primitives are canonical | **selected** |
| Images→PDF | requires Pillow policy | decompression-bomb, EXIF, alpha/background, animation, image→PDF semantics | standalone | later |
| WebP→PNG | requires Pillow policy | animation + alpha + decompression safety + multi-output publication | standalone | later |
| Files/Folders | stdlib but broad | traversal/filter/schema/error aggregation/export semantics | broad surface | later bounded slice |

Mixed Document Split wins because its primitive algorithms are already extracted. This slice can therefore prove cross-pack orchestration, partial-success reporting and typed batch composition without adding a new native/security dependency.

## Historical oracle

Legacy owner: `split_document_files_into_parts(...)` in `K Tools Neo - Versão Estável 2.py`.

Observed behavior:

- input is a sequence of paths;
- only existing `.md`, `.txt`, `.pdf` files are retained; unsupported/missing entries are filtered before processing;
- if no compatible inputs remain, fail;
- `parts >= 2` is required;
- destination directory is created;
- input order is preserved;
- every retained file receives an equal progress span `1 / total_files`;
- a child callback maps local `[0,1]` progress into that file's batch span and clamps values;
- `.pdf` dispatches to PDF split;
- `.md` / `.txt` dispatch to Text split;
- outputs are flattened in input order and in each splitter's part order;
- per-file exceptions are caught and accumulated as `"{filename}: {error}"` rather than aborting the remaining batch;
- if at least one output exists, the operation succeeds with outputs plus accumulated errors;
- if zero outputs exist, the operation raises a batch failure using up to the first five errors (or a no-output fallback);
- successful completion reports final progress 1.0;
- legacy result consumed by the UI exposes `outputs`, `errors`, `output_folder`, `input_count`, `output_count`.

V1 may normalize exact human-readable wording but must preserve filtering, ordered dispatch, equal-span progress mapping, continue-on-file-error, flattened output order, partial-success reporting and zero-output failure semantics.

## Package boundary

Create a new orchestration pack rather than placing mixed document policy inside core, Text or PDF:

```text
packages/ktools-documents/
  pyproject.toml
  src/ktools_documents/
    __init__.py
    batch.py        # orchestration/result/error owner
    api.py          # direct API projection
    node.py         # workflow adapter
```

Dependencies:

- `ktools-core>=0.1.0`
- `ktools-text>=0.1.0`
- `ktools-pdf>=0.1.0`

No Pillow/FFmpeg/native dependency is introduced.

## One-owner invariant

```text
                      ktools_documents.batch.split_documents_into_parts
                           /                                \
          ktools_text.splitter                       ktools_pdf.splitter
       split_text_file_into_parts                  split_pdf_into_parts
                           \                                /
                         ordered flattened batch result
                           /                                \
                     direct API                      workflow node
```

The documents pack owns only dispatch, aggregation, progress weighting and batch error/report policy.

It must not contain:

- text decoding or line-balancing logic;
- PDF reader/page-copy logic;
- primitive collision naming logic;
- primitive temp-publication logic.

## Domain result model

Introduce a JSON-safe result object/model for direct/internal use, e.g. `DocumentSplitBatchResult`, containing at minimum:

- `artifacts: tuple[Artifact, ...]` or equivalent ordered collection;
- `errors: tuple[str, ...]`;
- `input_count: int` — number of compatible files actually attempted;
- `output_count: int` — number of successfully published artifacts;
- `output_folder: str` — normalized local destination path/URI representation suitable for JSON projection.

The workflow node projects:

- `files: FILE_SET` — ordered successful output Artifacts;
- `report: JSON` — JSON-safe batch metadata excluding duplicate raw Artifact serialization unless needed.

Recommended report fields:

```json
{
  "inputCount": 3,
  "outputCount": 5,
  "errorCount": 1,
  "errors": ["bad.pdf: ..."],
  "outputFolder": "..."
}
```

This makes partial success explicit instead of hiding errors in logs or converting a partly successful batch into total workflow failure.

## Node contract

Type id: `document.split.files`

Input:

- `files: FILE_SET` — ordered local FILE/PDF Artifacts; runtime filters supported extensions `.md`, `.txt`, `.pdf` while preserving relative order.

Outputs:

- `files: FILE_SET` — flattened successful outputs in source order then part order;
- `report: JSON` — batch counts/errors/destination summary.

Config:

- `output_dir`: required destination directory;
- `parts`: integer >= 2; bool/non-integer rejected.

Version: `1`.
Cache policy: `NEVER`.

Reason: child splitters publish requested files and are themselves NEVER. Reusing a prior batch result would skip required publication and alter collision-safe repeat-run behavior.

## Artifact semantics

The orchestrator must preserve Artifacts emitted by the canonical child splitters rather than reconstructing weaker generic path objects.

Consequences:

- PDF outputs remain `Artifact.type == PDF` with PDF page-range metadata;
- Text outputs remain `Artifact.type == FILE` with Text chunk metadata/MIME;
- batch output FILE_SET may therefore contain heterogeneous file-like Artifact subtypes;
- provenance may identify the orchestrator run/node as producer only if child owners support an explicit parent-produced-by override without lying about execution; otherwise child invocation must use the orchestrator's current `run_id/node_id` as `produced_by` while preserving domain metadata.

V1 acceptance requires current workflow provenance to be coherent and ArtifactRegistry to snapshot the flattened nested outputs.

## Supported-input filtering

Legacy behavior filters unsupported/missing paths before batch execution rather than adding them to `errors`.

V1 preserves this distinction:

- compatible existing `.md/.txt/.pdf` files -> attempted;
- unsupported/missing/non-file entries -> ignored during compatibility filtering;
- zero compatible entries -> classified batch input error.

The node still rejects non-Artifact values or unsupported/non-local Artifact URI forms at its adapter boundary rather than silently accepting malformed runtime data.

## Partial success and failure semantics

There are two levels of partiality:

1. child splitters are per-output atomic but not set-wide transactional;
2. batch orchestrator is per-input tolerant and continues after one source file fails.

V1 therefore does **not** roll back:

- earlier parts of a failed source that were already atomically published by a child splitter;
- successful outputs from earlier source files.

However, only Artifacts actually returned by successful child calls are included in the batch's successful `files` output. If a child raises after publishing earlier parts, those orphaned partial child outputs may exist on disk but are not falsely claimed in the successful returned FILE_SET unless the child API itself returns them before failure (current child APIs do not).

If at least one child call returns outputs, the batch is a successful workflow node with `report.errors` describing failed sources.

If no child call returns any outputs, raise `DocumentSplitBatchError` and fail the node.

## Progress contract

Public direct API may accept `progress_callback(value: float, message: str)`.

For `N` compatible inputs:

- each input owns span `1/N`;
- child local progress is clamped to `[0,1]`;
- global progress is `base + local * span`;
- errors do not stop later source processing;
- successful partial batch still emits final 1.0 completion.

Progress is supplemental and must not own dispatch/ordering/error semantics.

## Diagnostics boundary

No new native/subprocess boundary exists, so full bespoke Diagnostics integration is not required in V1. Existing engine failure/journal/ArtifactRegistry evidence remains authoritative.

The batch report itself is product data, not diagnostics: expected per-source errors in a partial-success batch must remain queryable from the node's JSON output.

## Direct API

Expose a direct API that returns a structured result, not only a bare list of paths, because partial-success errors are part of the legacy product contract.

The direct route and workflow node must invoke the same batch owner and produce equivalent ordered outputs/report semantics under equivalent clean inputs.

## Acceptance

### A — legacy characterization / RED

- [ ] compatible input filtering preserves `.md/.txt/.pdf` order;
- [ ] zero compatible inputs fails;
- [ ] invalid `parts` fails;
- [ ] PDF/Text dispatch goes to canonical child owners;
- [ ] flattened outputs preserve source order then part order;
- [ ] one source failure does not stop later sources;
- [ ] partial success returns outputs + errors;
- [ ] zero successful outputs fails with classified batch error;
- [ ] progress spans compatible inputs equally and reaches 1.0 on partial/full success;
- [ ] result counts/folder/report shape characterized.

### B — architecture

- [ ] new `ktools-documents` pack depends on core/text/pdf;
- [ ] no primitive Text/PDF split algorithm exists in documents pack;
- [ ] direct API and node delegate to one batch owner;
- [ ] node is `document.split.files: FILE_SET -> FILE_SET + JSON`, v1 NEVER.

### C — Artifact / persistence

- [ ] child output Artifacts retain domain type/MIME/metadata;
- [ ] current orchestrator run/node provenance is coherent;
- [ ] ArtifactRegistry snapshots all successfully returned flattened outputs;
- [ ] partial-success errors remain present in JSON report;
- [ ] cached upstream `files.literal` may be reused while document split executes again.

### D — equivalence/composition

- [ ] direct API and node return equivalent output ordering/report counts on clean mixed fixture;
- [ ] real mixed fixture includes at least one Text and one PDF source;
- [ ] repeated execution collision-safely republishes child outputs;
- [ ] one deliberately bad compatible source plus later good source proves continue-after-error.

### E — hosted regression

- [ ] root CI installs `ktools-documents` after Text/PDF;
- [ ] Core/JSON/Text/PDF suites remain green;
- [ ] Documents suite passes Ubuntu/Windows Python 3.10/3.13;
- [ ] hosted mixed Document Split smoke reopens/verifies emitted Text/PDF artifacts and report;
- [ ] xyflow remains green.

## Non-goals

- rewriting Text/PDF splitter algorithms;
- image documents;
- recursive folder input;
- user-configurable per-file part counts;
- set-wide rollback/transactions;
- generalized fan-out/fan-in engine primitive;
- production UI/editor work;
- rewiring the stable GUI in this slice;
- Pillow policy or image conversion.

## Promotion rule

Promote only after discriminating RED, GREEN, architecture audit proving primitive delegation, hosted mixed smoke on Windows/Linux, memory closure and green terminal exact `main` HEAD.

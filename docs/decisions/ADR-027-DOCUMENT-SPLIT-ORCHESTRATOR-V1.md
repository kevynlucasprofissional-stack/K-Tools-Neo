# ADR-027 — Mixed Document Split is an orchestration Node Pack

Status: **PROVED / ACCEPTED FOR M5 SLICE 5**

## Context

The historical `split_document_files_into_parts(...)` surface accepts an ordered mixed batch of existing `.md`, `.txt` and `.pdf` files. It filters unsupported/missing inputs, gives every compatible source an equal progress span, dispatches Text and PDF work to format-specific splitters, continues after per-source failure, flattens successful outputs in source order, and exposes partial-success errors/counts to the UI.

By M5 Slice 5 both primitive branches already had canonical owners:

- Markdown/TXT split → `ktools-text`;
- PDF split → `ktools-pdf`.

Creating another mixed splitter would reintroduce duplicate transformation logic.

## Decision

`packages/ktools-documents/` is the canonical evolution owner for the **mixed-document batch orchestration boundary only**.

Its V1 node is:

```text
document.split.files
  files: FILE_SET
      -> files: FILE_SET
      -> report: JSON
```

Version `1`, `CachePolicy.NEVER`.

The package may own:

- supported-suffix filtering;
- ordered Text/PDF dispatch;
- equal-span progress weighting;
- per-source error aggregation;
- successful Artifact flattening;
- structured batch-result/report projection.

It must delegate primitive work directly to:

- `ktools_text.splitter.split_text_file_into_parts`;
- `ktools_pdf.splitter.split_pdf_into_parts`.

It must not own text decoding/balancing, PDF page copying, primitive collision naming or primitive atomic publication.

## Partial-success semantics

A per-source exception does not abort later compatible inputs.

If at least one child call returns outputs, the node succeeds and the JSON report carries the accumulated source errors. If no child call returns outputs, the batch fails with `DocumentSplitBatchError`.

Child splitters remain atomic per published output rather than set-wide transactional. A child may therefore leave already-published partial files on disk before raising; the orchestrator does not falsely include those files in its successful returned `FILE_SET` when the child did not return them.

## Artifact semantics

The orchestrator preserves the exact Artifacts returned by child owners instead of reconstructing generic path objects. Consequently:

- PDF members remain `DataType.PDF` with PDF MIME/page-range metadata;
- Text members remain `DataType.FILE` with Text MIME/chunk metadata;
- the heterogeneous file-like collection continues to use `FILE_SET` in V1;
- workflow calls pass current `run_id/node_id` as `produced_by`, allowing ArtifactRegistry to bind successful child outputs coherently to the orchestrator node.

No `DOCUMENT_SET`, `PDF_SET` or generalized fan-out abstraction is introduced by this slice.

## Cache decision

The orchestration node is `NEVER` because its contract includes child file publication. A prior successful batch result cannot be substituted without skipping required publication and collision-safe repeat-run behavior.

An upstream `files.literal` may still be cached; tests prove that this does not suppress the orchestrator or child publication.

## Evidence

- spec gate: `c3fe4b98bc923eeb02a0b47877262bcbf83620d9`, run `33661964413`, 5/5;
- discriminating RED: `3a60b6b4e73cf40d14f3da8b2de9d862402f76db`, run `33662320157`; prior Core/JSON/Text/PDF suites passed before Documents failed because `ktools_documents` did not exist;
- GREEN/audited technical candidate: `bde8b3789d86959b1218969510ed68aed14d410e`, run `33664355218`, 5/5;
- every Python lane installed `ktools-documents`, passed the Documents suite, and passed the real mixed Text/PDF workflow smoke;
- xyflow remained green.

## Compatibility debt

The stable monolithic GUI still contains the historical mixed dispatcher. It becomes a frozen compatibility path. New mixed-document orchestration semantics and bug fixes belong to `ktools-documents`; a later traditional Tool/UI migration should redirect the GUI surface to the canonical package rather than evolve both copies.

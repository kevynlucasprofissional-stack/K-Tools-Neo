# Final Report — Mixed Document Split Orchestrator V1

Status: **TECHNICALLY RESOLVED / TERMINAL CLOSURE CI PENDING**

## Objective

Extract the historical mixed Markdown/TXT/PDF batch split surface as orchestration over canonical `ktools-text` and `ktools-pdf`, preserving ordered partial-success/report semantics without creating another primitive splitter.

## Initial state

- Text Split terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` had passed run `33661273251` 5/5.
- PDF split was canonical in `ktools-pdf`.
- Markdown/TXT split was canonical in `ktools-text`.
- the stable monolith still owned mixed filtering/dispatch/progress/error aggregation.
- Images→PDF and WebP remained behind an unformalized Pillow safety boundary.
- Files/Folders remained a broader traversal/result-schema boundary.

## Discovery and hypotheses

Fresh comparison considered Mixed Document Split, Images→PDF, WebP→PNG and bounded Files/Folders.

The selected hypothesis was that Mixed Document Split had become a low-duplication orchestration slice because both primitive transformation branches already had canonical owners. This was accepted only after source inspection proved the remaining legacy behavior was filtering, dispatch, progress weighting, error aggregation and report construction.

Images→PDF/WebP were deferred because their correct extraction first requires explicit Pillow version/decompression-bomb, EXIF orientation, alpha/background and animation policy. Files/Folders was deferred because its traversal/filter/report surface remained materially broader.

## Specification

Spec gate `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` passed run `33661964413` 5/5.

Locked V1 contract:

```text
document.split.files
  files: FILE_SET
      -> files: FILE_SET
      -> report: JSON
```

Version 1, `CachePolicy.NEVER`.

Partial success is product state: one source may fail while later sources succeed, and the JSON report carries those errors. Zero successful child results is a node failure.

## RED

RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / run `33662320157` was discriminating.

On Ubuntu 3.13 the existing Core (76), JSON (64), Text (28) and PDF (24) suites passed before the new Documents suite failed because `ktools_documents` did not yet exist. This isolated the intended product boundary.

## Implementation

GREEN candidate `bde8b3789d86959b1218969510ed68aed14d410e` introduced:

- `packages/ktools-documents` with dependencies on core/text/pdf;
- `DocumentSplitBatchError`;
- `DocumentSplitBatchResult`;
- `batch.split_documents_into_parts(...)`;
- direct `api.split_document_files_into_parts(...)`;
- `document.split.files` workflow node;
- structured `report` output;
- root-CI install/test coverage;
- mixed Markdown/PDF hosted smoke.

The batch owner delegates all primitive work to `ktools_text.splitter.split_text_file_into_parts` and `ktools_pdf.splitter.split_pdf_into_parts`.

## Evidence

Run `33664355218` on exact candidate `bde8b3789d86959b1218969510ed68aed14d410e` passed **5/5**:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow spike.

All Python lanes installed the Documents pack, passed its tests and executed the real mixed Text/PDF smoke.

The test suite proves filtering/order, invalid-parts rejection, continue-after-error, partial-success reporting, zero-output failure, weighted progress, typed node contract, child Artifact preservation, current provenance, ArtifactRegistry snapshots, cached-source/republication behavior, direct/workflow equivalence and structural absence of primitive Text/PDF algorithms.

## Integration audit

**PASS**.

No second Text or PDF splitter exists in `ktools-documents`. The pack owns only mixed batch orchestration. Child Artifacts retain domain type/MIME/metadata. The heterogeneous result remains `FILE_SET`; no domain-specific collection or generalized fan-out abstraction was invented.

`document.split.files` remains NEVER because substituting a previous batch result would skip required file publication and alter repeat-run collision behavior.

## Regressions

No prior Core/JSON/Text/PDF or xyflow regression was observed in the hosted candidate. Existing smokes continued to pass in all lanes.

## Known debt / risk

- the stable GUI still contains the historical mixed dispatcher and is not yet rewired;
- child splitters and the batch are not set-wide transactional; already published child outputs may remain after later failure;
- orphaned outputs from a child that raises after publishing earlier parts may exist on disk but are not falsely returned as successful Artifacts;
- image capabilities remain gated on a formal Pillow safety/semantic contract.

## Memory

ADR: `docs/decisions/ADR-027-DOCUMENT-SPLIT-ORCHESTRATOR-V1.md`.

Canonical evidence: `docs/specs/document-split-orchestrator-v1/evidence.md`.

Canonical owner: `packages/ktools-documents` for mixed dispatch/aggregation/report semantics; `ktools-text` and `ktools-pdf` remain primitive split owners.

## Terminal state

**TECHNICALLY RESOLVED.**

The final promotion claim is intentionally withheld until the synchronized memory-closure HEAD itself passes the standard 5-job hosted CI gate. After that gate, Slice 5 becomes **RESOLVED / PROMOTED** and Slice 6 starts with fresh discovery.

# Evidence — Mixed Document Split Orchestrator V1

Status: **TECHNICALLY RESOLVED / TERMINAL MEMORY-CLOSURE CI PENDING**

## Prerequisite gate

Text Split V1 terminal closure:

- HEAD `4a52bef50653aa11878351645d122d0c0ab52343`;
- run `33661273251`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 4 was terminal-green before Slice 5 implementation began.

## Fresh discovery / selection evidence

The legacy `split_document_files_into_parts(...)` boundary was re-inspected after Text/PDF split primitives became canonical. It filters existing `.md/.txt/.pdf`, preserves source order, validates `parts >= 2`, creates the destination, assigns equal progress spans, dispatches PDF/Text work, catches errors per source, continues later inputs, flattens successful outputs, succeeds partially when at least one output exists, and reports outputs/errors/folder/input/output counts.

Candidate comparison selected Mixed Document Split over Images→PDF, WebP→PNG and bounded Files/Folders because it required no new transformation dependency or security/native boundary and could remove a real legacy owner strictly through orchestration.

Spec/plan gate:

- commit `c3fe4b98bc923eeb02a0b47877262bcbf83620d9`;
- hosted run `33661964413`;
- result **5/5 success**.

## Discriminating RED

RED commit:

`3a60b6b4e73cf40d14f3da8b2de9d862402f76db`

Run:

`33662320157`

Observed Ubuntu 3.13 boundary before failure:

- Core: 76 tests passed;
- JSON: 64 tests passed;
- Text: 28 tests passed;
- PDF: 24 tests passed;
- first new Documents step failed importing the deliberately absent `ktools_documents` package with `ModuleNotFoundError`.

The RED therefore discriminated at the intended missing-product boundary rather than packaging, runner or prior-regression failure.

## GREEN / architecture evidence

Technical candidate:

`bde8b3789d86959b1218969510ed68aed14d410e`

Run:

`33664355218`

Result: **5/5 success**.

Successful jobs:

- xyflow-spike;
- core Ubuntu / Python 3.10;
- core Ubuntu / Python 3.13;
- core Windows / Python 3.10;
- core Windows / Python 3.13.

Every Python lane reached and passed:

1. Install `ktools-core`;
2. Install `ktools-json`;
3. Install `ktools-text`;
4. Install `ktools-pdf`;
5. Install `ktools-documents`;
6. Core suite;
7. JSON suite;
8. Text suite;
9. PDF suite;
10. Documents suite;
11. all pre-existing workflow smokes;
12. `Documents mixed split workflow smoke`.

## Contract evidence

`packages/ktools-documents/tests/test_orchestrator_v1.py` proves:

- only existing `.md/.txt/.pdf` inputs are attempted;
- supported input order and child part order are preserved;
- `parts` bool/non-integer/<2 is rejected;
- one bad compatible source does not prevent a later valid source from running;
- partial success returns successful Artifacts plus report errors;
- zero successful child results fails with `DocumentSplitBatchError`;
- equal-span batch progress is bounded and completes at 1.0;
- node contract is `FILE_SET -> FILE_SET + JSON`, version 1, `NEVER`;
- Text outputs remain `FILE` Artifacts and PDF outputs remain `PDF` Artifacts;
- `produced_by` is current orchestrator run/node in workflow execution;
- ArtifactRegistry records strong snapshots for flattened child outputs;
- cached upstream `files.literal` does not suppress Documents execution or collision-safe re-publication;
- direct API and workflow paths are equivalent on independent clean destinations;
- source inspection guards against Text/PDF algorithm duplication in the documents pack.

## Hosted mixed smoke

`packages/ktools-documents/examples/run_mixed_split_workflow.py` creates a real Markdown file, a four-page PDF and an ignored `.bin` input, then executes:

```text
files.literal -> document.split.files
```

The smoke verifies:

- report `(inputCount=2, outputCount=4, errorCount=0)`;
- output Artifact types `[FILE, FILE, PDF, PDF]`;
- ordered Text parts concatenate back to the source;
- emitted PDFs reopen successfully;
- page dimensions/order are preserved as two two-page parts.

This smoke passed on Ubuntu and Windows under Python 3.10 and 3.13.

## Architecture audit

Audit result: **PASS**.

`ktools_documents.batch` calls exactly:

- `ktools_text.splitter.split_text_file_into_parts`;
- `ktools_pdf.splitter.split_pdf_into_parts`.

The package contains no Text decoding/balancing implementation, PDF reader/page-copy implementation, primitive collision allocator or primitive atomic writer. Direct API and workflow node both delegate to `batch.split_documents_into_parts`.

The orchestrator preserves child Artifacts rather than reconstructing weaker generic path records.

## Failure / transaction boundary

V1 has two explicit partiality levels:

- child Text/PDF splitters are atomic per published output, not set-wide transactional;
- Documents is tolerant per source and continues after one source fails.

A child that publishes earlier parts and later raises may leave those already-published files on disk. Because the child did not return them, the Documents successful `FILE_SET` does not falsely claim them. Successful outputs from other sources remain.

## Compatibility debt

The stable GUI still contains the historical mixed dispatcher. It is now compatibility debt. New mixed-document batch semantics/bug fixes belong to `packages/ktools-documents`; future Tool/UI migration should redirect the legacy surface rather than evolve both owners.

## Remaining promotion gate

The code candidate is technically green. Promotion becomes terminal only when the synchronized documentation/memory closure HEAD containing ADR-027, canonical state, roadmap, testing policy, known issues, journal, tasks/evidence/final report also passes the standard 5-job hosted CI gate.

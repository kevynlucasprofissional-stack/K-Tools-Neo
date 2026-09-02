# Spec — PDF Merge Node Pack V1

Status: **IMPLEMENTATION ACCEPTED / FINAL MEMORY CI PENDING**
Milestone: M5 — Official local Node Packs, Slice 2
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Extract the legacy PDF merge behavior into the first canonical PDF Node Pack and prove that multiple local PDF inputs can be validated, merged, safely published and represented as a first-class `PDF` Artifact through one shared direct-API/workflow owner.

Historical characterization source: `merge_pdf_files(...)` and its PDF helpers in `K Tools Neo - Versão Estável 2.py`.

## Why PDF merge is Slice 2

Discovery after Text Slice 1 re-inventoried real bounded owners rather than carrying forward a preselected feature.

Compared candidates:

| Candidate | Dependency boundary | Existing behavior complexity | Output shape | Slice-2 fit |
|---|---|---:|---|---:|
| PDF merge | `pypdf` (Python library) | moderate, bounded validation + publication | one PDF | **selected** |
| PDF split | `pypdf` | moderate, multi-output naming/partition policy | FILE_SET | later PDF slice |
| Images→PDF | Pillow + pypdf/image policy | higher | one PDF | later |
| WebP→PNG | Pillow + decompression/EXIF/alpha/animation policy | higher | FILE_SET | later Image pack |
| document split | mixed MD/TXT/PDF paths | broader semantic surface | multiple files/report | later |

PDF merge expands the product into a new capability family without introducing FFmpeg/native-process risk and without requiring a new typed collection beyond M5 Slice 1 `FILE_SET`.

## Characterized contract

The migrated V1 preserves/proves:

- ordered, non-empty PDF input sequence;
- source must exist, be a file and use `.pdf`;
- a single Path passed where a sequence is required fails explicitly rather than being iterated as path text;
- output suffix normalization to `.pdf`;
- output cannot be one of the inputs;
- output parent creation;
- `pypdf.PdfReader(..., strict=False)` through a checked reader owner;
- encrypted/protected inputs fail closed in V1;
- corrupt/incomplete/unreadable and zero-page PDFs fail with `PdfMergeError`;
- page order follows file order and page order within each file;
- same-directory temporary publication precedes `os.replace`;
- previous destination survives handled failure before final replacement;
- existing non-input destination is replaced on successful publication;
- progress callback remains supplementary and is forwarded by the direct API.

Exact binary identity is not a product contract. Semantic page count/order/dimensions are the deterministic test oracle for generated fixtures.

## Package boundary

Implemented:

```text
packages/ktools-pdf/
  pyproject.toml
  README.md
  examples/
    run_merge_workflow.py
  src/ktools_pdf/
    __init__.py
    reader.py
    writer.py
    api.py
    node.py
  tests/
    test_writer.py
    test_node.py
```

One-owner path:

```text
checked PDF reader + merge writer
            ↓
     writer.merge_pdf_files
       ↙              ↘
 direct API       pdf.merge.files
```

The node adapter contains no reader/page-copy/publication implementation.

## Node contract

Type id: `pdf.merge.files`

- input `files: FILE_SET` — ordered local FILE/PDF Artifacts;
- output `pdf: PDF` — published first-class PDF Artifact;
- config `output_path` — required destination; suffix normalized to `.pdf`;
- version `1`;
- cache policy `NEVER`.

Publication is required behavior, so an old cached Artifact cannot substitute for executing the node. A cached upstream `files.literal` remains independently reusable while the merge node executes again.

## Artifact semantics

The output Artifact:

- type `PDF`;
- normalized local `file://` URI;
- current `run_id/node_id` in `produced_by`;
- `application/pdf` MIME type;
- JSON-safe `sourceCount` and `totalPages` metadata.

M4 ArtifactRegistry strong-snapshots the local PDF output and records the current run/node/output occurrence as `EXECUTED`.

## Input and URI boundary

V1 reuses `FILE_SET`; no `PDF_SET` is introduced without a second real collection-type requirement.

Every member must be an Artifact of type FILE or PDF. Local URI interpretation is owned by `ktools_core.local_files.path_from_file_uri()`. `LocalFileUriError` is translated into the PDF domain taxonomy rather than reimplementing path parsing.

## Dependency boundary

`pypdf>=5,<7` is declared in `ktools-pdf` package metadata. Business logic never calls the legacy generic auto-installer.

`cryptography` is not added by default. Encrypted/protected PDFs fail closed in V1 rather than silently expanding dependency or decryption semantics.

## Publication safety

- same-directory temporary output;
- output/input collision rejected before publication;
- complete writer output precedes final replace;
- existing destination is replaced only after successful complete temp write;
- handled failure cleans temp output where possible and preserves the prior destination;
- writer/reader close attempts do not hide the primary failure;
- partial final output is never claimed as success.

## Diagnostics

No subprocess/native boundary exists in this slice. Engine lifecycle diagnostics already correlate node start/success/failure. Domain errors are classified through `PdfMergeError`; no duplicate noisy logging was added solely for checklist compliance.

## Acceptance

### A — characterization RED

- [x] empty input rejected;
- [x] missing/non-file/non-PDF rejected;
- [x] single path is not treated as a sequence;
- [x] output suffix normalization characterized;
- [x] output/input collision characterized;
- [x] ordered page concatenation characterized with deterministic tiny generated PDFs;
- [x] empty/no-readable-page PDF rejected;
- [x] protected/encrypted input fails closed with classified error;
- [x] prior destination survives handled pre-replacement failure;
- [x] successful publication replaces an existing non-input destination.

### B — package owner

- [x] `packages/ktools-pdf` exists with explicit `pypdf` dependency;
- [x] direct API delegates to shared writer;
- [x] direct API preserves progress callback;
- [x] workflow adapter delegates to same writer;
- [x] structural regression prevents duplicate page-copy/publication algorithm in adapter.

### C — workflow contract

- [x] `pdf.merge.files` accepts ordered FILE_SET;
- [x] local URI parsing reuses core owner;
- [x] output is PDF Artifact;
- [x] output provenance uses current run/node;
- [x] ArtifactRegistry records EXECUTED occurrence + strong snapshot;
- [x] node is NEVER and republishes on equivalent repeated runs even with cache injected;
- [x] cached `files.literal` upstream remains independently reusable while merge still executes.

### D — equivalence

- [x] direct API and workflow produce PDFs with identical page count/order/dimension semantics for equivalent fixtures;
- [x] exact binary byte identity is explicitly not required.

### E — hosted regression

- [x] root CI installs `ktools-pdf`;
- [x] PDF suite passes Ubuntu/Windows Python 3.10/3.13;
- [x] core/JSON/Text regressions remain green;
- [x] real PDF workflow smoke writes and reopens merged PDF and verifies exact page order dimensions;
- [x] xyflow remains green.

Accepted technical candidate: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`.
Hosted run: `33649789491` — five of five jobs success.

## Integration audit

- no pack-local `file://` parser;
- node adapter has no `PdfReader`, `PdfWriter` or `add_page` logic;
- dependency installation is package/bootstrap owned;
- PDF publication remains NEVER;
- Text/PDF both use temp-then-replace publication patterns, but their writers have materially different write semantics. Do not generalize a shared core abstraction yet; revisit after another file-producing pack proves a stable common contract.

## Canonical ownership / debt

After final memory promotion, `packages/ktools-pdf/` is the canonical evolution owner for PDF merge semantics. The historical function in `K Tools Neo - Versão Estável 2.py` remains a frozen compatibility path until traditional Tool/UI migration redirects it.

## Non-goals

PDF split, image→PDF, OCR, PDF compression, password cracking/decryption, broad PDF editing, visual-editor changes, full legacy GUI rewiring and cache replay of publication remain outside this slice.

## Promotion rule

Technical implementation/evidence is accepted. Final closure requires this synchronized canonical-memory HEAD to pass the same hosted matrix. After that, mark the slice RESOLVED / PROMOTED and begin fresh discovery for M5 Slice 3.

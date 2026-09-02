# Spec — PDF Merge Node Pack V1

Status: **ACTIVE / SPEC LOCKED**
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

## Characterization source

The legacy implementation establishes the following supported behavior to be proved before promotion:

- input is an ordered non-empty sequence of PDF paths;
- each source must exist, be a file and be a `.pdf`;
- output suffix is normalized to `.pdf`;
- output cannot be one of the inputs;
- output parent is created;
- `pypdf.PdfReader(..., strict=False)` is used through a checked reader helper;
- encrypted/protected PDFs are classified explicitly rather than merged blindly;
- PDFs with no readable pages are rejected;
- page order follows file order, then page order within each file;
- final publication is written through a temporary file and promoted only after successful complete writer output;
- previous destination must survive a handled failure before final replacement;
- progress callback is supplemental and owns no merge semantics.

Exact protected/corrupt error wording may be normalized inside the new package, but valid supported behavior and output ordering must remain equivalent.

## Package boundary

Create:

```text
packages/ktools-pdf/
  pyproject.toml
  README.md
  examples/
  src/ktools_pdf/
    __init__.py
    reader.py
    writer.py
    api.py
    node.py
  tests/
```

One-owner path:

```text
checked PDF reader + merge writer
            ↓
     writer.merge_pdf_files
       ↙              ↘
 direct API       pdf.merge.files
```

The node adapter must not reimplement reader validation, page-copy loops, output normalization or publication safety.

## Node contract

Type id:

`pdf.merge.files`

Input:

- `files: FILE_SET` — ordered FILE Artifacts whose local paths must resolve to supported PDFs.

Output:

- `pdf: PDF` — first-class PDF Artifact for the published output.

Config:

- `output_path` — required destination path/string; non-`.pdf` suffix is normalized to `.pdf`.

Version: `1`.

Cache policy: `NEVER`.

Reason: the contract includes publishing/replacing the requested destination. A previous cached Artifact reference is not equivalent to performing the requested side effect.

The pure semantic identity of source PDFs may later support a planning/inspection node if a real composition use-case requires it; V1 must not invent one just to make caching look attractive.

## Artifact semantics

The output Artifact:

- uses type `PDF`;
- uses normalized local `file://` URI;
- identifies current `run_id/node_id` in `produced_by`;
- records JSON-safe useful metadata such as source count and total page count;
- uses MIME type `application/pdf`.

M4 ArtifactRegistry must be able to strong-snapshot the output because `PDF` is a file subtype and local-file validity already supports file Artifacts.

## Input type boundary

V1 deliberately reuses `FILE_SET` rather than introducing `PDF_SET` before a second real typed-collection need exists.

The adapter validates every member at runtime:

- must be an `Artifact`;
- Artifact type must be `FILE` or `PDF` where semantically appropriate;
- URI must be local through `ktools_core.local_files.path_from_file_uri()`;
- local path must pass PDF validation.

Do not duplicate file URI parsing in the PDF pack.

## Dependency boundary

`pypdf` is a package-level dependency of `ktools-pdf`, not a dynamic auto-install hidden inside business logic.

The new package must not copy the monolith's generic `ensure_package()` installation behavior. Environment/bootstrap owns dependency installation; capability execution owns domain behavior.

No `cryptography` dependency is added merely by default unless evidence proves a supported encrypted-PDF behavior requires it. Encrypted inputs may fail closed with a classified error in V1.

## Publication safety

- same-directory temporary output;
- previous destination replaced only after successful complete write;
- output/input collision rejected before write;
- cleanup of temporary output after handled failure where possible;
- writer close/finalization must not hide the primary failure;
- no partial final output claimed as success.

## Diagnostics

This slice has no subprocess/native boundary. Existing engine lifecycle diagnostics cover node start/success/failure.

Add domain-specific diagnostics only if they convey useful operational facts not already present, such as source/page counts or a classified protected/corrupt-PDF boundary. Do not duplicate noise.

## Acceptance

### A — characterization RED

- [ ] empty input rejected;
- [ ] missing/non-file/non-PDF rejected;
- [ ] output suffix normalization characterized;
- [ ] output/input collision characterized;
- [ ] ordered page concatenation characterized with deterministic tiny fixture PDFs;
- [ ] empty/no-readable-page PDF rejected where reproducible;
- [ ] protected/encrypted input fails closed with classified error;
- [ ] prior destination survives handled pre-replacement failure.

### B — package owner

- [ ] `packages/ktools-pdf` exists with explicit `pypdf` dependency;
- [ ] direct API delegates to shared writer;
- [ ] workflow adapter delegates to same writer;
- [ ] structural regression prevents duplicate page-copy/publication algorithm in adapter.

### C — workflow contract

- [ ] `pdf.merge.files` accepts ordered FILE_SET;
- [ ] local URI parsing reuses core owner;
- [ ] output is PDF Artifact;
- [ ] output provenance uses current run/node;
- [ ] ArtifactRegistry records EXECUTED occurrence + strong snapshot;
- [ ] node is NEVER and republishes on equivalent repeated runs even with cache injected;
- [ ] cached `files.literal` upstream remains independently reusable while merge still executes.

### D — equivalence

- [ ] direct API and workflow produce PDFs with identical page count/order/content semantics for equivalent fixtures;
- [ ] exact binary byte identity is not required unless pypdf proves deterministic at that level; semantic PDF equivalence is the acceptance criterion.

### E — hosted regression

- [ ] root CI installs `ktools-pdf`;
- [ ] PDF suite passes Ubuntu/Windows Python 3.10/3.13;
- [ ] core/JSON/Text regressions remain green;
- [ ] real PDF workflow smoke writes and reopens a merged PDF with expected page count/order marker;
- [ ] xyflow remains green.

## Non-goals

- PDF split in the same slice;
- image→PDF;
- OCR;
- PDF compression;
- password cracking/decryption;
- broad PDF editing;
- visual editor changes;
- rewiring the entire legacy GUI;
- cache replay of the publication node.

## Promotion rule

Promote only after discriminating RED, GREEN, integration audit, exact-head Windows/Linux + xyflow hosted evidence, explicit canonical ownership/debt classification, merge and post-merge `main` verification.
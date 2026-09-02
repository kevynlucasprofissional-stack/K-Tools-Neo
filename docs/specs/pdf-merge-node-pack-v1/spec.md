# Spec — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**
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
| PDF merge | `pypdf` | moderate, bounded validation + publication | one PDF | **selected** |
| PDF split | `pypdf` | moderate, multi-output naming/partition policy | FILE_SET | later PDF slice |
| Images→PDF | Pillow + image policy | higher | one PDF | later |
| WebP→PNG | Pillow + decompression/EXIF/alpha/animation policy | higher | FILE_SET | later Image pack |
| document split | mixed MD/TXT/PDF paths | broader semantic surface | multiple files/report | later |

PDF merge expands the product into a new capability family without introducing FFmpeg/native-process risk and without requiring a new typed collection beyond `FILE_SET`.

## Characterized contract

V1 proves/preserves:

- ordered non-empty PDF input sequence;
- source must exist, be a file and use `.pdf`;
- one Path passed instead of a sequence fails explicitly;
- output suffix normalizes to `.pdf`;
- output cannot be one of the inputs;
- output parent is created;
- `pypdf.PdfReader(..., strict=False)` is used through a checked reader owner;
- encrypted/protected PDFs fail closed in V1;
- corrupt/incomplete/unreadable and zero-page PDFs fail with `PdfMergeError`;
- page order follows file order then page order within each file;
- final publication uses same-directory temporary output followed by `os.replace`;
- previous destination survives handled failure before final replace;
- an existing non-input destination is replaced after successful complete publication;
- progress callback is supplementary and preserved by the direct API.

Semantic page count/order/structure is the deterministic equivalence contract; exact PDF bytes are not.

## Package boundary

```text
packages/ktools-pdf/
  pyproject.toml
  README.md
  examples/run_merge_workflow.py
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

The node adapter does not reimplement reader validation, page-copy loops, output normalization or publication safety.

## Node contract

Type id: `pdf.merge.files`

- input `files: FILE_SET` — ordered local FILE/PDF Artifacts;
- output `pdf: PDF` — first-class published PDF Artifact;
- config `output_path` — required destination, normalized to `.pdf`;
- version `1`;
- cache policy `NEVER`.

Reason: publication/replacement of the requested destination is required behavior. Cached metadata cannot substitute for that side effect. A cached upstream `files.literal` remains independently reusable while merge executes again.

## Artifact semantics

Output Artifact uses type `PDF`, normalized local `file://` URI, current `run_id/node_id` provenance, MIME `application/pdf`, and JSON-safe `sourceCount`/`totalPages` metadata.

M4 ArtifactRegistry records the output occurrence as EXECUTED and strong-snapshots the local PDF.

## Input / URI boundary

V1 deliberately reuses `FILE_SET`; `PDF_SET` is deferred until a second concrete typed-collection requirement appears.

Each member must be an Artifact of type FILE or PDF. URI resolution uses `ktools_core.local_files.path_from_file_uri()`; the pack translates `LocalFileUriError` into `PdfMergeError` rather than copying platform path parsing.

## Dependency boundary

`pypdf>=5,<7` is declared by `ktools-pdf`; business logic never invokes the legacy generic auto-installer.

`cryptography` is not added by default. Encrypted/protected PDFs fail closed in V1. Password/decryption semantics require a dedicated future spec.

## Publication safety

- same-directory temporary output;
- output/input collision rejected before write;
- complete writer output precedes final replace;
- prior destination survives handled pre-replacement failure;
- successful complete publication may replace an existing non-input destination;
- temp cleanup is attempted after handled failure;
- reader/writer close attempts do not hide primary failures;
- partial final output is never claimed as success.

## Diagnostics

No subprocess/native boundary exists. Existing engine lifecycle diagnostics cover start/success/failure and the pack normalizes domain failures through `PdfMergeError`. No duplicate noisy logging or unsupported causal-diagnosis claim is added.

## Acceptance

### A — characterization RED

- [x] empty input rejected;
- [x] missing/non-file/non-PDF rejected;
- [x] one Path is not silently treated as an input sequence;
- [x] output suffix normalization characterized;
- [x] output/input collision characterized;
- [x] ordered page concatenation characterized with deterministic generated PDFs;
- [x] empty/no-readable-page PDF rejected;
- [x] protected/encrypted input fails closed;
- [x] prior destination survives handled pre-replacement failure;
- [x] existing non-input destination is replaced on successful publication.

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
- [x] node is NEVER and republishes on equivalent repeated runs with cache injected;
- [x] cached `files.literal` upstream remains independently reusable while merge executes.

### D — equivalence

- [x] direct API and workflow produce PDFs with identical page count/order/dimension semantics for equivalent fixtures;
- [x] exact binary identity is explicitly not required.

### E — hosted regression

- [x] root CI installs `ktools-pdf`;
- [x] PDF suite passes Ubuntu/Windows Python 3.10/3.13;
- [x] core/JSON/Text regressions remain green;
- [x] real PDF workflow smoke writes and reopens merged PDF and verifies page order;
- [x] xyflow remains green;
- [x] synchronized canonical-memory HEAD passes the same five-job matrix.

## Evidence checkpoints

- spec gate: `081dac1380361761bf38e2914db495138e4c9b76`, run `33631531313` green;
- RED: `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271` discriminating PDF-test failure;
- initial GREEN: `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`, run `33649227197` 5/5;
- technical candidate: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491` 5/5 including PDF smoke;
- synchronized memory candidate: `8600b0adda1bba2a460da9fee8f45b7a02b41f9b`, run `33650661761` 5/5.

## Integration audit

No duplicate pack-local `file://` parser exists. Adapter contains no `PdfReader`, `PdfWriter` or page-copy implementation. Dependency installation is package-owned. Publication remains NEVER.

Text/PDF both use temp-then-replace patterns, but their writer semantics differ. A shared core publication abstraction is intentionally deferred until another file-producing pack proves a stable cross-domain contract.

## Canonical ownership / debt

`packages/ktools-pdf/` is the canonical evolution owner for PDF merge behavior.

`K Tools Neo - Versão Estável 2.py` still contains the historical implementation. It is frozen compatibility debt, not an independent semantic owner. New fixes/features originate in `ktools-pdf`; later traditional Tool/UI migration must redirect or retire the old path.

## Non-goals

PDF split, image→PDF, OCR, compression, password cracking/decryption, broad PDF editing, visual-editor changes, full legacy GUI rewiring and cache replay of publication remain outside V1.

## Terminal state

**RESOLVED / PROMOTED.** All RED/GREEN/refactor, hosted, audit and synchronized-memory gates are satisfied. M5 may advance to fresh Slice 3 discovery.

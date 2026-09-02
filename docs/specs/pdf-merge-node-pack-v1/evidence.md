# Evidence — PDF Merge Node Pack V1

Status: **TECHNICAL CANDIDATE ACCEPTED / FINAL MEMORY CI PENDING**

## Slice selection

After Text Node Pack V1 promotion, bounded legacy owners were re-inventoried. PDF merge was selected over PDF split, Images→PDF, WebP→PNG and mixed document split because it opens a new product family through one bounded Python dependency (`pypdf`) and one output Artifact without adding Pillow or FFmpeg/native-process policy.

Text prerequisite closure: `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`, five jobs success.

Spec checkpoint: `081dac1380361761bf38e2914db495138e4c9b76`; run `33631531313` passed before behavior code began.

## Discriminating RED

RED commit: `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`.
Run: `33648993271`.

The hosted Ubuntu/Python 3.13 lane proved the harness/dependency boundary before failing:

- checkout/setup succeeded;
- editable installs of core, JSON, Text and PDF succeeded;
- `pypdf 6.16.2` installed from the declared package dependency;
- 72 core tests passed;
- 64 JSON tests passed;
- 15 Text tests passed;
- first red product boundary was `PDF node pack tests`;
- 11 PDF tests ran red because `writer.merge_pdf_files` deliberately raised `NotImplementedError` and `pdf.merge.files` was deliberately unregistered.

This is accepted as a product RED, not a packaging/runner failure.

## Initial GREEN

Implementation commit: `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`.
Run: `33649227197`.

All five hosted jobs succeeded:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow.

The four Python lanes installed `ktools-pdf`, passed core/JSON/Text/PDF suites and existing smokes.

## Hardening / accepted technical candidate

Hardening commit: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`.
Run: `33649789491`.
Result: **5/5 success**.

Hardening added/proved:

- direct API forwards the supplementary progress callback;
- a single Path is rejected rather than accidentally treated as an input sequence;
- root CI runs a real PDF workflow smoke;
- smoke creates deterministic source PDFs, executes `files.literal -> pdf.merge.files`, reopens the output and asserts ordered page dimensions `(101x201, 102x202, 301x401)`;
- PDF smoke and verification pass in Ubuntu/Windows Python 3.10/3.13;
- xyflow remains green.

Current PDF suite contains 13 tests (8 writer/characterization + 5 node/integration tests).

## Behavior evidence

Tests prove:

- empty/missing/directory/non-PDF input rejection;
- explicit rejection of one Path passed instead of an input collection;
- `.pdf` output normalization;
- output/input collision protection;
- deterministic file-order then page-order concatenation;
- zero-page and encrypted/protected inputs fail closed;
- corrupt input fails before final replace and preserves previous destination;
- existing non-input destination is replaced after successful complete publication;
- direct API preserves progress callback;
- output Artifact is `PDF`, `application/pdf`, local URI, with source/page metadata;
- `pdf.merge.files` is FILE_SET -> PDF, version 1, NEVER;
- current run/node provenance is attached;
- ArtifactRegistry records EXECUTED output with strong snapshot;
- `files.literal` may be CACHED while `pdf.merge.files` executes again;
- direct API/workflow semantic page order is equivalent;
- direct API/node delegate to `writer.merge_pdf_files`;
- adapter contains no `PdfReader`, `PdfWriter` or `add_page` algorithm;
- local URI interpretation remains owned by `ktools-core`.

## Dependency / diagnostics boundary

`pypdf>=5,<7` is an explicit package dependency. No business-logic auto-installer exists in the pack. `cryptography` was not added by default; encrypted inputs fail closed in V1.

There is no subprocess/native boundary, so M3 engine lifecycle diagnostics are sufficient for V1. Errors are normalized through `PdfMergeError`; no unsupported claim of automatic causal diagnosis is made.

## Ownership boundary

Canonical evolution owner after final closure: `packages/ktools-pdf/`.

The old stable GUI still contains historical PDF merge code. It is compatibility debt, not a second semantic owner. Future PDF merge changes originate in `ktools-pdf`; later Tool/UI migration must redirect or retire the old path.

## Pending promotion evidence

The synchronized memory commit created from this evidence must itself pass the same five-job hosted matrix. That final run will close P-013 and move Slice 2 to RESOLVED / PROMOTED.

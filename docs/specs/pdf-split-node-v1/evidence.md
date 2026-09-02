# Evidence — PDF Split Node V1

Status: **RESOLVED / PROMOTED**

## Prerequisite gate

PDF Merge V1 terminal closure:

- HEAD `e3a3934aada29e185de7da18cf413ceaa3c299e8`;
- run `33651923578`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 2 was closed before Slice 3 implementation began.

## Discovery evidence

Fresh discovery compared PDF split, Images→PDF, WebP→PNG, mixed Document Split and Files/Folders scan.

PDF split was selected because it:

- reuses the accepted `pypdf` dependency and checked-reader/atomic-publication boundary;
- adds a genuine one-file-input/multi-file-output workflow contract;
- produces an ordered FILE_SET whose members remain first-class PDF Artifacts;
- is already called by the legacy mixed Document Split, so extraction removes a prerequisite for a later orchestration slice;
- introduces no new native/subprocess/image-security boundary.

Images→PDF and WebP→PNG remain later candidates because they introduce Pillow-specific EXIF/alpha/animation/decompression policy. Document Split is better sequenced after PDF/Text primitives are canonical. Files/Folders scan remains a broad traversal/report contract needing its own bounded spec.

## Characterized legacy semantics

The accepted V1 behavior preserves:

- one local PDF source;
- `parts >= 2` with bool/non-integer rejected at node config boundary;
- checked reader and fail-closed protected/corrupt/empty behavior;
- parts clamped to page count;
- balanced contiguous ranges (`5 -> 3` gives `2/2/1`);
- `{stem}_parte_XX_de_YY.pdf` naming;
- `_1`, `_2`, ... collision suffixes without overwrite;
- per-part atomic publication;
- ordered output paths/Artifacts;
- supplemental progress callback;
- explicit partial-set failure semantics: earlier atomic parts may remain when a later part fails, but the failing destination is not left partial or claimed successful.

## RED

Commit `e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`.

Discrimination:

- package installation succeeded;
- Core suite succeeded;
- JSON suite succeeded;
- Text suite succeeded;
- existing PDF Merge tests succeeded;
- new PDF Split tests failed at the intended product boundary because `file.literal`, `split_pdf_into_parts` and `pdf.split.parts` were absent.

This is accepted product RED rather than CI/bootstrap RED.

## GREEN

Commit `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925`, run `33653824159`, passed all five jobs:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow.

Proved:

- `file.literal: -> FILE`, version 1, PURE;
- source cache invalidation after file mutation;
- `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- split output members are PDF Artifacts with current run/node provenance and page-range metadata;
- ArtifactRegistry strong snapshots of nested PDF outputs;
- cached source does not suppress split publication;
- repeated execution collision-safely produces new names;
- direct/workflow semantic equivalence;
- split→merge recreates page order/count.

## Integration hardening

Commit `cb25cad6e6d60377d07a0c4d761700d7785f0c1e`, run `33654265424`, passed 5/5.

Additional proofs:

- structural test: `file.literal` and `files.literal` share `_local_file_artifact` rather than duplicating Artifact creation/path validation;
- multi-output failure boundary: forced second-part publication failure leaves the first already-published atomic part, leaves no failed second destination and no temp residue;
- hosted real `file.literal -> pdf.split.parts -> pdf.merge.files` smoke added to all Python matrix lanes;
- the smoke generates a five-page PDF, reopens the three parts to verify `2/2/1`, then reopens the recomposed PDF to verify original ordered dimensions.

## Architecture evidence

Canonical owner:

```text
ktools_pdf.splitter.split_pdf_into_parts
          ↑                   ↑
       direct API       pdf.split.parts node
```

The node adapter contains no page partition/copy algorithm. Checked PDF reading and atomic PDF publication remain shared package boundaries.

## FILE_SET decision evidence

No `PDF_SET` was required. The real end-to-end split→merge workflow proves that an ordered `FILE_SET` containing typed PDF Artifacts carries sufficient runtime truth and composes directly with `pdf.merge.files`. Specialized typed collections remain deferred until a future graph-time element-type requirement demonstrates real value.

## Promotion status

Technical implementation and integration gates are satisfied. Canonical closure commit is required to carry this evidence into CURRENT_STATE/ROADMAP/ADR/journal and then must itself pass terminal hosted CI.

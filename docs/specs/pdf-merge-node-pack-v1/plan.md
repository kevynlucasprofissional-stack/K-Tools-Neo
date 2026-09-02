# Plan — PDF Merge Node Pack V1

Status: **ACTIVE**

## Sequence

1. Characterize the current legacy PDF merge behavior with deterministic fixtures and explicit failure cases.
2. Record a RED that fails because the new package/node contract does not yet exist, not because of packaging or CI infrastructure.
3. Implement `packages/ktools-pdf` with explicit `pypdf` dependency and one shared merge writer.
4. Add `pdf.merge.files: FILE_SET -> PDF` as a thin adapter with `CachePolicy.NEVER`.
5. Prove output Artifact provenance and M4 ArtifactRegistry strong snapshot.
6. Prove upstream `files.literal` cache reuse does not suppress PDF publication.
7. Add root CI install/tests and a real PDF workflow smoke.
8. Run integration audit for duplicate reader/path/publication logic and unnecessary dependency leakage.
9. Synchronize canonical memory, obtain exact-head hosted evidence, promote, merge and verify `main`.

## Design constraints

- Reuse `FILE_SET`; do not introduce `PDF_SET` without a second real collection-type requirement.
- Reuse `ktools_core.local_files.path_from_file_uri()`; no pack-local URI parser.
- Do not dynamic-install `pypdf` from business logic.
- Do not classify publication as PURE.
- Do not require byte-identical PDF binaries when semantic page equivalence is the stable contract.
- Preserve same-directory temp publication and input/output collision safety.
- Protected/corrupt inputs fail closed with explicit errors.
- Do not modify imported app internals or the production visual editor.

## Evidence strategy

Use small generated PDFs produced by `pypdf.PdfWriter` in tests so fixtures are deterministic and repository-light. Give pages distinct dimensions/metadata markers where needed to prove order semantically after reopen.

Hosted proof must execute the real package and node on Ubuntu/Windows Python 3.10/3.13. xyflow remains a regression lane, not implementation evidence for PDF behavior.
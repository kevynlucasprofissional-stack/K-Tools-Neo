# Plan — PDF Split Node V1

Status: **ACTIVE**

## Sequence

1. Lock Slice 3 after fresh candidate comparison.
2. Add a discriminating RED for legacy PDF split behavior plus the new `file.literal`/node contracts.
3. Refactor builtin local-file Artifact creation so `file.literal` and `files.literal` share one owner.
4. Extend `ktools-pdf` with `splitter.split_pdf_into_parts` reusing checked reader and atomic PDF publication.
5. Add thin direct API and `pdf.split.parts` node adapter.
6. Prove PDF Artifacts inside FILE_SET, nested ArtifactRegistry snapshots and NEVER/cache semantics.
7. Prove direct/workflow semantic equivalence.
8. Prove `file.literal -> pdf.split.parts -> pdf.merge.files` end-to-end composition.
9. Add hosted split smoke/composition evidence to root CI.
10. Audit duplicate page/collision/publication logic and cross-domain abstraction pressure.
11. Synchronize canonical memory and require exact-head terminal CI.

## Design constraints

- extend `packages/ktools-pdf`; do not create another PDF package;
- input cardinality is one FILE, not a one-element FILE_SET convention;
- add `file.literal` rather than weakening node cardinality;
- no `PDF_SET` in V1; output members remain typed PDF Artifacts inside FILE_SET;
- reuse `ktools_core.local_files`/builtin local Artifact logic;
- reuse `open_pdf_reader_checked` and `write_pdf_writer_atomic`;
- publication node is NEVER;
- preserve collision-safe non-overwrite naming;
- no hidden dependency installation;
- no broad GUI migration.

## Evidence strategy

Generate tiny PDFs with distinct page dimensions using `pypdf.PdfWriter`.

Use 5-page fixtures to prove 3-part balancing as 2/2/1 and dimensions to prove contiguous order after reopen. Use separate clean directories for direct/workflow equivalence. Use a shared output directory for repeated-run collision behavior.

Hosted proof must exercise real file paths and reopen generated PDFs rather than assert only object metadata.

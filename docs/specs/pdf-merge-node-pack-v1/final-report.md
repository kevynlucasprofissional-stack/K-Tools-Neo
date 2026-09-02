# Final Report — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**

## Objective

Migrate the bounded legacy PDF merge behavior into the platform using one canonical package owner shared by direct API and workflow execution, with first-class PDF Artifact semantics and safe publication.

## Initial state

- PDF merge existed only in the large stable GUI monolith.
- FILE_SET, PDF type, ArtifactRegistry, cache semantics and diagnostics already existed from M0-M5 Slice 1.
- No official PDF Node Pack existed.
- Legacy dependency installation was dynamic and unsuitable as a capability boundary.

## Discovery

PDF merge was selected after comparing PDF split, Images→PDF, WebP→PNG and mixed document split. It is bounded, depends on pure-Python `pypdf`, produces one PDF Artifact and avoids introducing image/native-process complexity prematurely.

## Hypotheses and results

- **FILE_SET is sufficient for ordered PDF merge V1 — validated.** Runtime member validation distinguishes FILE/PDF Artifacts without premature `PDF_SET`.
- **Publication must remain NEVER — validated.** Cached source may be reused, but requested destination publication always executes.
- **Dependency installation belongs to package/bootstrap — validated.** Hosted RED installed pypdf from metadata before PDF behavior failed.
- **Semantic PDF equivalence is the right deterministic oracle — validated.** Reopened generated fixtures prove page order/structure without incidental binary identity.
- **Adapter should not own URI/reader/page-copy logic — validated.** Core owns URI parsing; PDF reader/writer own domain behavior.
- **Encrypted-PDF support should expand automatically — rejected for V1.** Protected inputs fail closed without implicit cryptography/decryption policy.

## Implemented

- `packages/ktools-pdf` with explicit `pypdf>=5,<7`;
- checked reader and `PdfMergeError` taxonomy;
- ordered merge writer;
- same-directory temporary publication and final replace;
- direct API with progress callback forwarding;
- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- PDF Artifact provenance, MIME and source/page metadata;
- ArtifactRegistry strong-snapshot integration;
- cache/lifecycle proof showing cached source + executed publication;
- deterministic generated-PDF tests;
- real hosted PDF workflow smoke and reopen verification.

## Evidence

Spec gate: `081dac1380361761bf38e2914db495138e4c9b76`, run `33631531313` green.

RED: `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`, first product failure at PDF tests after successful dependencies and 72 core + 64 JSON + 15 Text tests.

Initial GREEN: `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`, run `33649227197`, five jobs success.

Accepted technical candidate: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491`, five jobs success including PDF workflow smoke/verification in every Python lane.

Synchronized memory candidate: `8600b0adda1bba2a460da9fee8f45b7a02b41f9b`, run `33650661761`, five jobs success.

Full evidence: `docs/specs/pdf-merge-node-pack-v1/evidence.md`.

## Integration audit

No duplicate local URI parser or reader/page-copy algorithm exists in the adapter. Package dependency is explicit. Publication remains side-effectful/NEVER. Progress surface from the characterized legacy contract is preserved. Text/PDF temp-publication similarity is recorded for observation rather than prematurely abstracted.

## Remaining debt

The stable GUI still invokes historical PDF merge logic. `ktools-pdf` is canonical; GUI rewiring is a later Tool-surface migration. PDF split, image→PDF, WebP→PNG, OCR/compression and encrypted-PDF decryption remain outside V1.

## Terminal state

**RESOLVED / PROMOTED.**

All implementation, hosted regression, audit and synchronized-memory gates are satisfied. M5 may advance to fresh Slice 3 discovery.

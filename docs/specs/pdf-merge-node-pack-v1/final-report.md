# Final Report — PDF Merge Node Pack V1

Status: **CANDIDATE FINAL REPORT / FINAL MEMORY CI PENDING**

## Objective

Migrate the bounded legacy PDF merge behavior into the platform using one canonical package owner shared by direct API and workflow execution, with first-class PDF Artifact semantics and safe publication.

## Initial state

- PDF merge existed only in the large stable GUI monolith.
- FILE_SET, PDF type, ArtifactRegistry, cache semantics and diagnostics already existed from M0-M5 Slice 1.
- No official PDF Node Pack existed.
- Legacy dependency installation was dynamic and unsuitable as a capability boundary.

## Discovery

PDF merge was selected after comparing PDF split, Images→PDF, WebP→PNG and mixed document split. The selected slice is bounded, depends on pure-Python `pypdf`, produces one PDF Artifact and avoids introducing image/native-process complexity prematurely.

## Hypotheses / results

### H1 — FILE_SET is sufficient for ordered PDF merge V1
Validated. Runtime member validation distinguishes FILE/PDF Artifacts without introducing premature `PDF_SET` covariance.

### H2 — publication must remain NEVER
Validated. The requested destination must be produced/replaced on every run; cached metadata cannot substitute for that side effect. Upstream `files.literal` can still be independently CACHED.

### H3 — pypdf should be a package dependency, not installed from capability code
Validated. Hosted RED installed `pypdf 6.16.2` through package metadata before reaching PDF tests.

### H4 — semantic PDF equivalence is the correct deterministic oracle
Validated. Generated pages with distinct dimensions prove source/page ordering after reopen without requiring incidental byte-for-byte writer identity.

### H5 — a pack-local URI parser or page loop in the adapter is unnecessary
Validated. URI conversion is reused from `ktools-core`; reader/page-copy/publication remain in the PDF package owner, and the adapter delegates to `writer.merge_pdf_files`.

### H6 — encrypted PDF support should expand dependencies automatically
Rejected for V1. Protected/encrypted inputs fail closed. No implicit cryptography/decryption policy is introduced without a dedicated requirement.

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

Full evidence: `docs/specs/pdf-merge-node-pack-v1/evidence.md`.

## Integration audit

- no duplicate local URI parser;
- no reader/writer/page-copy algorithm in node adapter;
- package dependency is explicit;
- publication remains side-effectful/NEVER;
- progress surface from the legacy contract is preserved;
- direct single-Path misuse is rejected explicitly;
- Text/PDF temp-publication similarity is observed but not abstracted prematurely because their writer contracts differ.

## Remaining debt

The stable GUI still invokes historical PDF merge logic. `ktools-pdf` becomes the canonical evolution owner after final closure; GUI rewiring is a later Tool-surface migration.

PDF split, image→PDF, WebP→PNG, OCR/compression and encrypted-PDF decryption remain outside V1.

## Terminal state

**TECHNICALLY RESOLVED; canonical-memory promotion pending.**

The only remaining gate is the synchronized documentation/memory HEAD passing the same five-job hosted matrix. After that, mark Slice 2 RESOLVED / PROMOTED and select Slice 3 through fresh discovery.

# ADR-024 — PDF Merge Node Pack V1 ownership and publication boundary

Status: **PROVED / ACCEPTED**
Milestone: M5 Slice 2 — RESOLVED / PROMOTED

## Decision

`packages/ktools-pdf/` is the canonical evolution owner for PDF merge behavior.

The V1 workflow node is `pdf.merge.files: FILE_SET -> PDF`, version `1`, with `CachePolicy.NEVER`.

## Reasons

1. PDF merge is a publication operation. Even when source/page transformation is deterministic, reusing an old Artifact would skip creation/replacement of the requested destination.
2. `pypdf` is an explicit package dependency (`>=5,<7`), not dynamically installed from business logic.
3. V1 reuses ordered `FILE_SET`; a new `PDF_SET` is deferred until another real collection contract proves it necessary.
4. FILE/PDF Artifact URIs reuse `ktools_core.local_files.path_from_file_uri()`; Node Packs do not own platform URI parsing.
5. Encrypted/protected PDFs fail closed in V1. No implicit `cryptography`, decryption or password policy is introduced without a dedicated requirement.
6. Deterministic acceptance is semantic PDF equivalence (reopened page count/order/structure), not incidental binary identity from a serializer.
7. Output publication uses a same-directory temporary file and final replace; a handled pre-replacement failure must preserve the previous destination.

## Evidence

- RED: `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`.
- Initial GREEN: `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`, run `33649227197` 5/5.
- Technical candidate: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491` 5/5.
- Synchronized memory gate: `8600b0adda1bba2a460da9fee8f45b7a02b41f9b`, run `33650661761` 5/5.

## Legacy boundary

`K Tools Neo - Versão Estável 2.py` still contains historical PDF merge logic. It is a frozen compatibility path, not an independent semantic owner. New PDF merge fixes/features originate in `ktools-pdf`; later traditional Tool/UI migration must redirect or retire the historical path.

## Revisit

Revisit `PDF_SET`, encrypted-PDF support, shared atomic-publication abstraction or pure PDF planning nodes only when concrete subsequent capabilities create a proved need.

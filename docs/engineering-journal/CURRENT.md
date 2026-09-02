# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 are preserved at `docs/engineering-journal/archive/2026-08-platform-foundation.md`.

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

## H-008 — One-owner capability architecture works with real product behavior
Status: **VALIDATED** — direct API and workflow nodes can share one implementation owner.

## H-009 — Durable execution should be injected, not mandatory database state
Status: **VALIDATED FOR V1**.

## H-010 — Events are execution history; tables are query projections
Status: **VALIDATED FOR SQLITE V1**.

## H-011 — Interrupted must remain distinct from Failed
Status: **VALIDATED**.

## H-012 — Durable observability needs conservative serialization
Status: **VALIDATED / SECURITY HARDENING**.

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis
Status: **VALIDATED** — RunJournal owns lifecycle truth; Diagnostics owns forensic/support evidence.

## H-014 — Diagnostics must be prerequisite, not cleanup
Status: **VALIDATED AS SEQUENCING RULE**.

## H-015 — Support bundles reconstruct facts, not causal certainty
Status: **VALIDATED**.

## H-016 — Crash evidence must be durable before finalization
Status: **VALIDATED FOR V1**.

## H-017 — Prior success is not reusable-result proof
Status: **REFUTED / REPLACED** — reuse requires PURE policy + semantic signature + valid outputs.

## H-018 — Size + mtime are hints, not strong content identity
Status: **VALIDATED** — SHA-256 closes same-size/restored-mtime mutation.

## H-019 — Cacheability must be capability-owned and fail-open
Status: **VALIDATED FOR M4 V1**.

## H-020 — CACHED must be a first-class lifecycle fact
Status: **VALIDATED**.

## H-021 — Real cache proof should separate pure computation from publication side effects
Status: **VALIDATED** — JSON planning caches; JSON/Text/PDF publication remains NEVER where required.

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct
Status: **VALIDATED FOR V1**.

## H-023 — Restart recovery is a new run until ownership is proved
Status: **ACCEPTED SAFETY BOUNDARY**.

## H-024 — Multi-file workflows need an honest ordered type
Status: **VALIDATED** — FILE_SET is the current exact ordered collection contract.

## H-025 — A source can be PURE while downstream publication remains NEVER
Status: **VALIDATED IN TEXT + PDF** — cached `files.literal` does not suppress required destination publication.

## H-026 — Green behavior tests do not prove architectural single ownership
Status: **VALIDATED / AUDIT LESSON** — integration audit is still required after tests turn green.

## H-027 — Legacy source of truth can become characterization source before UI rewiring
Status: **ACCEPTED MIGRATION BOUNDARY** — canonical package owners may coexist temporarily with frozen legacy compatibility paths.

## H-028 — Semantic document equivalence can be stronger than binary identity
Status: **VALIDATED IN PDF MERGE V1** — reopened page count/order/dimensions are the deterministic product oracle; serializer bytes are not assumed semantic.

## H-029 — Dependencies belong to package/bootstrap boundaries, not capability execution
Status: **VALIDATED IN PDF MERGE V1** — hosted RED installed pypdf from package metadata before behavior tests.

## H-030 — Encryption support should not expand implicitly
Status: **ACCEPTED PDF V1 SAFETY BOUNDARY** — protected/encrypted PDFs fail closed until a dedicated spec defines support.

## H-031 — Similar temp-publication code is not sufficient reason to generalize
Status: **ACTIVE DESIGN WATCH** — Text/PDF writers differ materially; revisit after another file-producing pack proves a stable common abstraction.

## E-004 — Correct output-collision guard can make non-isolated smoke red
Status: **CLASSIFIED** — fix isolation, not safety behavior.

## E-005 — GitHub Actions Node runtime warning
Status: **RESOLVED**.

## E-006 — Artifact signature regression initially compared only post-mutation state
Status: **RESOLVED / TEST-DESIGN LESSON**.

## E-007 — Internal cache markers can collide with legitimate user JSON
Status: **RESOLVED / SERIALIZATION HARDENING**.

## E-008 — Text RED proved contract absence rather than packaging failure
Status: **RESOLVED / USEFUL RED**.

## E-009 — Duplicate local-file URI parser survived GREEN until integration audit
Status: **RESOLVED / REFACTOR LESSON**.

## E-010 — PDF Merge RED proved dependency/bootstrap before behavior
Status: **RESOLVED / USEFUL RED** — `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`, reached intentionally red PDF tests after dependencies and prior suites passed.

## M5 Slice 1 closure

Text Node Pack V1 promotion merge `958d5bf563cda21673d69865d1508831c599c006` passed post-merge run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed run `33631040505`.

## M5 Slice 2 closure

PDF Merge V1 technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c` passed run `33649789491` 5/5, including real PDF workflow/reopen verification in every Python lane.

Synchronized memory candidate `8600b0adda1bba2a460da9fee8f45b7a02b41f9b` passed run `33650661761` 5/5.

Result: **Slice 2 RESOLVED / PROMOTED**. `packages/ktools-pdf` is canonical; legacy GUI PDF merge is compatibility debt.

## Next journal focus — M5 Slice 3

1. re-inventory remaining actual legacy owners rather than inheriting a favorite candidate;
2. compare PDF split, Images→PDF, WebP→PNG, mixed document split and bounded Files/Folders operations;
3. judge composition value relative to dependency/native policy and side-effect complexity;
4. do not introduce `PDF_SET` or generic atomic-publication abstraction without a proved need;
5. preserve direct API + workflow one-owner architecture;
6. integrate diagnostics at native/subprocess boundaries from the start;
7. if FFmpeg/FFprobe enters scope, establish the shared diagnostic process boundary before broad media nodes.

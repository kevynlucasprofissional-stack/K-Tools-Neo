# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 are preserved at `docs/engineering-journal/archive/2026-08-platform-foundation.md`.

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

## H-008 — One-owner capability architecture works with real product behavior
Status: **VALIDATED** — JSON split proves direct API and workflow nodes can share one implementation owner.

## H-009 — Durable execution should be injected, not mandatory database state
Status: **VALIDATED FOR V1** — `WorkflowEngine` accepts optional RunJournal; Memory/SQLite consume the same contract.

## H-010 — Events are execution history; tables are query projections
Status: **VALIDATED FOR SQLITE V1**.

## H-011 — Interrupted must remain distinct from Failed
Status: **VALIDATED** — unfinished state is not process-death proof.

## H-012 — Durable observability needs conservative serialization
Status: **VALIDATED / SECURITY HARDENING** — unknown objects avoid arbitrary repr/reflection; diagnostics redacts secrets; cache uses explicit envelopes.

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis
Status: **VALIDATED** — RunJournal owns lifecycle truth; Diagnostics owns richer forensic/support evidence.

## H-014 — Diagnostics must be prerequisite, not cleanup
Status: **VALIDATED AS SEQUENCING RULE** — future native/subprocess/integration capabilities include diagnostics in Definition of Done.

## H-015 — Support bundles reconstruct facts, not causal certainty
Status: **VALIDATED**.

## H-016 — Crash evidence must be durable before finalization
Status: **VALIDATED FOR V1**.

## H-017 — Prior success is not reusable-result proof
Status: **REFUTED / REPLACED** — reuse requires PURE policy + semantic signature + valid outputs.

## H-018 — Size + mtime are invalidation hints, not strong content identity
Status: **VALIDATED** — SHA-256 detects same-size restored-mtime mutation.

## H-019 — Cacheability must be capability-owned and fail-open
Status: **VALIDATED FOR M4 V1** — default NEVER; explicit PURE only.

## H-020 — CACHED must be a first-class lifecycle fact
Status: **VALIDATED** — no fake NODE_STARTED on reuse.

## H-021 — Real cache proof should separate pure computation from publication side effects
Status: **VALIDATED WITH JSON NODE PACK** — `json.split.plan` caches; `json.split` republishes.

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct
Status: **VALIDATED FOR V1**.

## H-023 — Restart recovery is a new run until ownership is proved
Status: **ACCEPTED SAFETY BOUNDARY**.

## H-024 — Multi-file workflows need an honest ordered type
Status: **VALIDATED IN M5 TEXT SLICE** — `FILE_SET` avoids smuggling ordered Artifact sequences through JSON/ANY.

## H-025 — A source can be PURE while downstream publication remains NEVER
Status: **VALIDATED IN M5 TEXT + PDF** — `files.literal` may be reused after strong validation while Text/PDF publication nodes execute again.

## H-026 — Green behavior tests do not prove architectural single ownership
Status: **VALIDATED / AUDIT LESSON** — Text integration review found duplicate local-file URI parsing and centralized it before promotion.

## H-027 — Legacy source of truth can become characterization source before UI rewiring
Status: **ACCEPTED MIGRATION BOUNDARY** — canonical package ownership can be established while old GUI copies remain explicitly frozen compatibility debt.

## H-028 — Semantic document equivalence can be stronger than binary identity
Status: **VALIDATED IN PDF MERGE V1** — generated PDF fixtures are reopened and page dimensions/order are asserted. Serializer byte identity is not treated as product semantics without a requirement.

## H-029 — Dependencies belong to package/bootstrap boundaries, not capability execution
Status: **VALIDATED IN PDF MERGE V1** — hosted RED installed `pypdf` from `pyproject.toml`; PDF business logic contains no generic auto-installer.

## H-030 — Encryption support should not expand implicitly
Status: **ACCEPTED PDF V1 SAFETY BOUNDARY** — protected/encrypted PDFs fail closed. Do not add cryptography/decryption/password behavior without a dedicated spec.

## H-031 — Similar temp-publication code is not sufficient reason to generalize
Status: **ACTIVE DESIGN WATCH** — Text and PDF both temp-write then replace, but their writer/finalization contracts differ. Revisit after a third file-producing pack proves a stable common API.

## E-004 — Correct output-collision guard can make non-isolated smoke red
Status: **CLASSIFIED** — fix test isolation, not safety behavior.

## E-005 — GitHub Actions Node runtime warning
Status: **RESOLVED** — root Actions moved to v7 generation.

## E-006 — Artifact signature regression initially compared only post-mutation state
Status: **RESOLVED / TEST-DESIGN LESSON**.

## E-007 — Internal cache markers can collide with legitimate user JSON
Status: **RESOLVED / SERIALIZATION HARDENING**.

## E-008 — M5 Text RED proved contract absence rather than packaging failure
Status: **RESOLVED / USEFUL RED** — run `33626957901` failed only on intentionally absent FILE_SET/files.literal contracts after setup/install.

## E-009 — Duplicate local-file URI parser survived GREEN until integration audit
Status: **RESOLVED / REFACTOR LESSON** — centralized before Text promotion.

## E-010 — PDF Merge RED proved dependency/bootstrap before behavior
Status: **RESOLVED / USEFUL RED** — commit `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`: core/JSON/Text/PDF installs succeeded, `pypdf 6.16.2` installed, 72 core + 64 JSON + 15 Text tests passed, then intentionally unimplemented PDF tests failed.

## M4 closure

M4 canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed run `33625955613`; formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

## M5 Slice 1 closure

Text Node Pack V1 promotion merge `958d5bf563cda21673d69865d1508831c599c006` passed post-merge run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed run `33631040505`.

## M5 Slice 2 closure candidate

PDF Merge V1 accepted technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c` passed run `33649789491` on Ubuntu/Windows Python 3.10/3.13 plus xyflow. Every Python lane reached and passed PDF tests, real PDF workflow smoke and reopened page-order verification.

Remaining gate: synchronized canonical-memory HEAD must pass the same five-job matrix before Slice 2 is marked fully RESOLVED / PROMOTED.

## Next journal focus — M5 Slice 3

After PDF closure:

1. re-inventory remaining actual legacy owners rather than inheriting a favorite candidate;
2. compare PDF split, Images→PDF, WebP→PNG, mixed document split and bounded Files/Folders operations;
3. prefer the slice that expands composability while keeping dependency/native policy explicit;
4. do not introduce PDF_SET or a generic atomic-publication abstraction without a proved second/third contract need;
5. preserve direct Tool/API + workflow one-owner architecture;
6. integrate diagnostics at native/subprocess boundaries rather than after bugs appear;
7. if FFmpeg/FFprobe enters scope, establish the shared diagnostic process boundary before broad media nodes.

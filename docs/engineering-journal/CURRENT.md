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
Status: **VALIDATED IN TEXT + PDF** — cached file sources do not suppress required destination publication.

## H-026 — Green behavior tests do not prove architectural single ownership
Status: **VALIDATED / AUDIT LESSON** — integration audit is still required after tests turn green.

## H-027 — Legacy source of truth can become characterization source before UI rewiring
Status: **ACCEPTED MIGRATION BOUNDARY** — canonical package owners may coexist temporarily with frozen legacy compatibility paths.

## H-028 — Semantic document equivalence can be stronger than binary identity
Status: **VALIDATED IN PDF** — reopened page count/order/dimensions are the deterministic product oracle; serializer bytes are not assumed semantic.

## H-029 — Dependencies belong to package/bootstrap boundaries, not capability execution
Status: **VALIDATED IN PDF** — hosted RED installed pypdf from package metadata before behavior tests.

## H-030 — Encryption support should not expand implicitly
Status: **ACCEPTED PDF V1 SAFETY BOUNDARY** — protected/encrypted PDFs fail closed until a dedicated spec defines support.

## H-031 — Similar temp-publication code is not sufficient reason to generalize
Status: **ACTIVE DESIGN WATCH** — Text/PDF writers differ materially; revisit only after another file-producing pack proves a stable common abstraction.

## H-032 — Singular cardinality should not be encoded as a one-item collection convention
Status: **VALIDATED IN PDF SPLIT V1** — `file.literal: -> FILE` plus `pdf.split.parts: FILE -> FILE_SET` keeps graph semantics honest and avoids runtime singleton assertions masquerading as type safety.

## H-033 — Typed Artifact members can postpone domain-specific collection types
Status: **VALIDATED FOR CURRENT PDF COMPOSITION** — FILE_SET containing PDF Artifacts composes split→merge across hosted Windows/Linux lanes without PDF_SET. Introduce specialized collections only when graph-time member typing proves necessary.

## H-034 — Multi-output publication needs an explicit transaction boundary
Status: **VALIDATED / SAFETY BOUNDARY** — PDF split is atomic per part, not all-or-nothing across the set. Earlier completed outputs may remain after a later failure; the failing output must not be partial or falsely claimed.

## H-035 — Composition tests are stronger than isolated contract tests for cardinality decisions
Status: **VALIDATED** — hosted `FILE -> FILE_SET -> PDF` split→merge proved source cardinality, member Artifact typing, publication and downstream consumption together.

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

## E-011 — PDF Split RED isolated the intended missing product contracts
Status: **RESOLVED / USEFUL RED** — `e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`, kept Core/JSON/Text and existing PDF Merge green while the new suite failed on missing `file.literal`, split API/node and shared owner.

## E-012 — Multi-output failure semantics cannot be inferred from atomic single-output writer tests
Status: **RESOLVED / TEST-DESIGN LESSON** — Slice 3 added a forced second-part publication failure proving earlier completed output retention, failed-destination absence and temp cleanup.

## M5 Slice 1 closure

Text Node Pack V1 promotion `958d5bf563cda21673d69865d1508831c599c006` passed run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed `33631040505`.

Result: **Slice 1 RESOLVED / PROMOTED**.

## M5 Slice 2 closure

PDF Merge V1 terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` passed run `33651923578` 5/5.

Result: **Slice 2 RESOLVED / PROMOTED**. `packages/ktools-pdf` became canonical for PDF merge; legacy GUI merge became compatibility debt.

## M5 Slice 3 closure

Spec gate `a09d600924aa66d031cc2bcc2f59feb04bdf0704` passed `33652921999` 5/5.

RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831` discriminated at the new PDF split product boundary.

GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159` passed 5/5.

Hardened technical candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424` passed 5/5, including hosted split→merge in Ubuntu/Windows Python 3.10/3.13.

Result pending only this memory-closure HEAD gate: **Slice 3 RESOLVED / PROMOTED**. `packages/ktools-pdf` is canonical for balanced PDF split; stable GUI merge/split copies are compatibility debt.

## Next journal focus — M5 Slice 4

After the Slice-3 closure HEAD is green:

1. re-inventory remaining legacy owners from the exact terminal main;
2. compare Images→PDF, WebP→PNG, mixed Document Split and bounded Files/Folders operations;
3. specifically test the hypothesis that Document Split is now a low-duplication orchestration slice because Text/PDF primitives exist — do not assume it without inspecting its non-PDF behavior and output/error contract;
4. if an image capability is selected, specify Pillow version/decompression-bomb policy, EXIF orientation, alpha/background semantics and animation behavior before implementation;
5. preserve one-owner direct API + workflow architecture and explicit publication/cache policy;
6. do not generalize FILE_SET, atomic publication or domain collection types without new evidence;
7. if FFmpeg/FFprobe enters scope later, establish the shared diagnostic process boundary before broad media nodes.

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
Status: **VALIDATED IN TEXT + PDF + DOCUMENTS** — cached file sources do not suppress required destination publication.

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
Status: **VALIDATED IN PDF SPLIT V1** — `file.literal: -> FILE` plus split `FILE -> FILE_SET` keeps graph semantics honest.

## H-033 — Typed Artifact members can postpone domain-specific collection types
Status: **VALIDATED FOR PDF/TEXT/DOCUMENTS COMPOSITION** — FILE_SET carries Text FILE and PDF Artifacts through isolated and mixed flows without specialized collection types.

## H-034 — Multi-output publication needs an explicit transaction boundary
Status: **VALIDATED / SAFETY BOUNDARY** — PDF and Text split are atomic per part, not all-or-nothing across the set. Earlier completed outputs may remain after a later failure; the failing output must not be partial or falsely claimed.

## H-035 — Composition tests are stronger than isolated contract tests for cardinality decisions
Status: **VALIDATED** — hosted FILE/FILE_SET compositions prove source cardinality, member Artifact flow, publication and downstream consumption together.

## H-036 — Similar file formats may require intentionally different decode policies
Status: **VALIDATED IN TEXT SPLIT V1** — Text Merge and Text Split have different legacy fallback orders. Deduplication is not allowed to silently erase caller-specific semantics.

## H-037 — Extract primitives before extracting an orchestrator
Status: **VALIDATED AS M5 SEQUENCING RULE** — mixed Document Split became a clean dispatch/aggregation problem only after PDF Split and Text Split had canonical owners.

## H-038 — Partial success can be product state rather than diagnostics
Status: **VALIDATED IN DOCUMENT SPLIT V1** — one source failure with later successful sources is a successful batch whose JSON report carries errors/counts. Converting every child failure into whole-node failure would erase legacy product semantics.

## H-039 — Cross-pack orchestrators should preserve child Artifacts, not reconstruct them
Status: **VALIDATED IN DOCUMENT SPLIT V1** — preserving returned Text/PDF Artifacts keeps type, MIME, metadata and provenance richer than rebuilding generic path records at the orchestration layer.

## H-040 — Orchestration does not justify a generalized workflow primitive by itself
Status: **VALIDATED / ANTI-OVERGENERALIZATION RULE** — `ktools-documents` needed supported-suffix dispatch, progress weighting and batch error/report semantics, but did not prove a reusable generic fan-out/fan-in engine abstraction. Generalize only after another independent use case exposes a stable shared contract.

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
Status: **RESOLVED / USEFUL RED** — `e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`, kept prior boundaries green while the new suite failed on missing single-file/split contracts.

## E-012 — Multi-output failure semantics cannot be inferred from atomic single-output writer tests
Status: **RESOLVED / TEST-DESIGN LESSON** — forced later-part failures prove earlier completed output retention, failed-destination absence and temp cleanup.

## E-013 — Text Split RED isolated product absence and preserved merge compatibility
Status: **RESOLVED / USEFUL RED** — `14a950d8d1b23412d7ba27dace66759d8ae2b37e`, run `33657352636`, failed at new Text Split contracts while existing Text Merge behavior remained the compatibility baseline.

## E-014 — Documents RED isolated orchestration absence after all primitive suites passed
Status: **RESOLVED / USEFUL RED** — `3a60b6b4e73cf40d14f3da8b2de9d862402f76db`, run `33662320157`, reached the Documents suite only after Core/JSON/Text/PDF passed and failed because `ktools_documents` did not exist. This proved a missing orchestration product boundary rather than child-regression failure.

## E-015 — Direct/workflow equivalence must separate semantic result from destination identity
Status: **RESOLVED / TEST-DESIGN LESSON** — independent direct/workflow fixtures intentionally publish into different clean directories. Equivalence compares report semantics excluding `outputFolder`, validates each destination separately, and compares child content/page semantics. Requiring literal destination equality would incorrectly punish test isolation.

## M5 Slice 1 closure

Text Node Pack V1 promotion `958d5bf563cda21673d69865d1508831c599c006` passed run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed `33631040505`.

Result: **Slice 1 RESOLVED / PROMOTED**.

## M5 Slice 2 closure

PDF Merge V1 terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` passed run `33651923578` 5/5.

Result: **Slice 2 RESOLVED / PROMOTED**. `packages/ktools-pdf` became canonical for PDF merge; legacy GUI merge became compatibility debt.

## M5 Slice 3 closure

Spec gate `a09d600924aa66d031cc2bcc2f59feb04bdf0704` passed `33652921999` 5/5.
RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831` discriminated at PDF split product absence.
GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159` passed 5/5.
Hardened candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424` passed 5/5.
Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870` passed 5/5.

Result: **Slice 3 RESOLVED / PROMOTED**.

## M5 Slice 4 closure

Spec gate `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` passed `33656954591` 5/5.
RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636` discriminated at Text Split product absence.
GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057` passed 5/5.
Hardened candidate `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733` passed 5/5.
Terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251` passed 5/5.

Result: **Slice 4 RESOLVED / PROMOTED**. `packages/ktools-text` is canonical for balanced Text split; stable GUI copies are compatibility debt.

## M5 Slice 5 closure

Fresh discovery selected mixed Document Split only after comparing Images→PDF, WebP→PNG and bounded Files/Folders and proving the remaining legacy surface was orchestration rather than a third transformation algorithm.

Spec gate `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` passed `33661964413` 5/5.

RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157` discriminated at Documents package/orchestration absence after prior Core/JSON/Text/PDF suites passed.

GREEN/audited technical candidate `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218` passed 5/5. All four Python lanes installed `ktools-documents`, passed the Documents suite and passed the real mixed Markdown/PDF workflow smoke.

Architecture result: `packages/ktools-documents` owns filtering/dispatch/progress/error aggregation/reporting only; primitive Text/PDF split ownership remains in `ktools-text`/`ktools-pdf`; partial-success errors are product-visible JSON; child Artifacts are preserved; Documents is NEVER; cached upstream sources do not suppress re-publication.

Result pending only this synchronized memory-closure HEAD gate: **Slice 5 RESOLVED / PROMOTION CLOSURE GATE**.

## Next journal focus — M5 Slice 6

After the Slice-5 closure HEAD is green:

1. re-inventory remaining owners from the exact terminal `main` rather than carrying a stale candidate ranking;
2. compare Images→PDF, WebP→PNG and bounded Files/Folders operations by behavior clarity, dependency/security boundary, side effects, Artifact shape, cacheability, diagnostics and duplicate-owner reduction;
3. if image work wins, lock Pillow range, decompression-bomb policy, EXIF orientation, alpha/background, animation/multiframe and collision/publication semantics before RED;
4. if Files/Folders wins, lock traversal roots, recursion, hidden files, symlink/reparse behavior, ordering, permission/OSError aggregation and report schema before implementation;
5. preserve child/primitive ownership and avoid generic abstractions until at least a second independent use case proves them;
6. do not change FILE_SET covariance or introduce domain collection types without a graph-time requirement;
7. if FFmpeg/FFprobe enters scope later, establish the shared diagnostic process boundary before broad media nodes.

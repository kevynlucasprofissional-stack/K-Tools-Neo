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
Status: **VALIDATED** — deterministic computation may cache; required file publication remains NEVER unless replay is proved.

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct
Status: **VALIDATED FOR V1**.

## H-023 — Restart recovery is a new run until ownership is proved
Status: **ACCEPTED SAFETY BOUNDARY**.

## H-024 — Multi-file workflows need an honest ordered type
Status: **VALIDATED** — FILE_SET is the current exact ordered collection contract.

## H-025 — A source can be PURE while downstream publication remains NEVER
Status: **VALIDATED IN TEXT + PDF + DOCUMENTS + IMAGES** — cached file sources do not suppress required destination publication.

## H-026 — Green behavior tests do not prove architectural single ownership
Status: **VALIDATED / AUDIT LESSON** — integration audit is still required after tests turn green.

## H-027 — Legacy source of truth can become characterization source before UI rewiring
Status: **ACCEPTED MIGRATION BOUNDARY** — canonical package owners may coexist temporarily with frozen legacy compatibility paths.

## H-028 — Semantic document equivalence can be stronger than binary identity
Status: **VALIDATED IN PDF** — reopened page count/order/dimensions are the deterministic product oracle; serializer bytes are not assumed semantic.

## H-029 — Dependencies belong to package/bootstrap boundaries, not capability execution
Status: **VALIDATED IN PDF + IMAGES** — pypdf/Pillow are installed from package/bootstrap boundaries before behavior execution.

## H-030 — Encryption support should not expand implicitly
Status: **ACCEPTED PDF V1 SAFETY BOUNDARY** — protected/encrypted PDFs fail closed until a dedicated spec defines support.

## H-031 — Similar temp-publication code is not sufficient reason to generalize
Status: **ACTIVE DESIGN WATCH** — Text/PDF/Images all use temp→promote patterns but still expose materially different writer, collision and aggregate/per-output contracts.

## H-032 — Singular cardinality should not be encoded as a one-item collection convention
Status: **VALIDATED IN PDF SPLIT V1** — `file.literal: -> FILE` plus split `FILE -> FILE_SET` keeps graph semantics honest.

## H-033 — Typed Artifact members can postpone domain-specific collection types
Status: **VALIDATED FOR PDF/TEXT/DOCUMENTS/IMAGES** — FILE_SET carries typed PDF and IMAGE members plus Text FILE members without specialized collection types.

## H-034 — Multi-output publication needs an explicit transaction boundary
Status: **VALIDATED / SAFETY BOUNDARY** — PDF split, Text split and WebP→PNG are atomic per output, not all-or-nothing across the set.

## H-035 — Composition tests are stronger than isolated contract tests for cardinality decisions
Status: **VALIDATED** — hosted workflows prove source cardinality, member Artifact flow, publication and downstream/runtime behavior together.

## H-036 — Similar file formats may require intentionally different decode policies
Status: **VALIDATED IN TEXT SPLIT V1** — Text Merge and Text Split have different legacy fallback orders; deduplication may not erase caller-specific semantics.

## H-037 — Extract primitives before extracting an orchestrator
Status: **VALIDATED AS M5 SEQUENCING RULE** — mixed Document Split became a clean dispatch/aggregation problem only after PDF/Text splitters had canonical owners.

## H-038 — Partial success can be product state rather than diagnostics
Status: **VALIDATED IN DOCUMENT SPLIT V1** — source failures can be successful batch state when the product report explicitly carries errors/counts.

## H-039 — Cross-pack orchestrators should preserve child Artifacts, not reconstruct them
Status: **VALIDATED IN DOCUMENT SPLIT V1** — preserving child Artifacts keeps type, MIME, metadata and provenance richer than rebuilding generic paths.

## H-040 — Orchestration does not justify a generalized workflow primitive by itself
Status: **VALIDATED / ANTI-OVERGENERALIZATION RULE** — one fan-out/fan-in use case did not prove a reusable generic orchestration engine.

## H-041 — A bounded first capability can establish a reusable safety foundation
Status: **VALIDATED IN IMAGE SLICE 6** — WebP→PNG was small enough to isolate Pillow versioning, bomb limits, EXIF and frame policy before Images→PDF adds aggregate-output semantics.

## H-042 — Format semantics can live in member Artifact metadata without a specialized collection port
Status: **VALIDATED IN IMAGE SLICE 6** — IMAGE Artifact type plus PNG MIME, frame policy, orientation, mode and dimensions were sufficient inside FILE_SET; no IMAGE_SET evidence emerged.

## H-043 — Security-sensitive decoder policy is product behavior, not an implementation detail
Status: **VALIDATED IN IMAGE SLICE 6** — the 80M-pixel ceiling, bomb-warning handling and Pillow major range are explicit tested contracts and must not be silently changed by future image capabilities.

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
Status: **RESOLVED / USEFUL RED** — `29a90cb7c2085b22d0cf3e345b39fecb6c050b76` / `33648993271` reached PDF product tests after dependencies/prior suites passed.

## E-011 — PDF Split RED isolated the intended missing product contracts
Status: **RESOLVED / USEFUL RED** — `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831` preserved prior boundaries while new split contracts failed.

## E-012 — Multi-output failure semantics cannot be inferred from atomic single-output writer tests
Status: **RESOLVED / TEST-DESIGN LESSON** — forced later failures prove earlier output retention, failed-destination absence and temp cleanup.

## E-013 — Text Split RED isolated product absence and preserved merge compatibility
Status: **RESOLVED / USEFUL RED** — `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`.

## E-014 — Documents RED isolated orchestration absence after all primitive suites passed
Status: **RESOLVED / USEFUL RED** — `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157` reached Documents only after Core/JSON/Text/PDF passed.

## E-015 — Direct/workflow equivalence must separate semantic result from destination identity
Status: **RESOLVED / TEST-DESIGN LESSON** — isolated output directories are correct; equivalence compares semantics/content rather than literal destination paths.

## E-016 — Image RED must prove Pillow bootstrap before missing product failure
Status: **RESOLVED / USEFUL RED** — `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304` observed Core 76 + JSON 64 + Text 28 + PDF 24 + Documents 7 passing, Pillow 12.3.0 installing, then Image failing exactly at missing `ktools_images`.

## M5 Slice 1 closure

Text promotion `958d5bf563cda21673d69865d1508831c599c006` / `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` / `33631040505`.
Result: **RESOLVED / PROMOTED**.

## M5 Slice 2 closure

PDF Merge terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` / `33651923578`, 5/5.
Result: **RESOLVED / PROMOTED**.

## M5 Slice 3 closure

Spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704` / `33652921999`; RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831`; GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159`; hardened `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424`; terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870`, 5/5.
Result: **RESOLVED / PROMOTED**.

## M5 Slice 4 closure

Spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`; RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`; GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`; hardened `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`; terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.
Result: **RESOLVED / PROMOTED**.

## M5 Slice 5 closure

Fresh discovery selected mixed Document Split only after comparing image/filesystem alternatives and proving the remaining boundary was orchestration.
Spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`; RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`; GREEN `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`; terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.
Result: **RESOLVED / PROMOTED**. `ktools-documents` owns batch orchestration only; Text/PDF primitives remain canonical child owners.

## M5 Slice 6 closure

Fresh discovery selected WebP→PNG over Images→PDF and bounded Files/Folders to establish the image safety foundation first.

Spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / `33666227293` passed 5/5.
RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304` discriminated at absent Image package after prior suites and Pillow bootstrap passed.
GREEN/audited technical candidate `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076` passed 5/5, including `ktools-images` suite and real generated RGB/RGBA WebP→PNG workflow smoke on every Python lane.

Architecture result: `ktools-images` owns Pillow safety/EXIF and WebP→PNG conversion; direct API/node share one converter; output members remain IMAGE Artifacts inside FILE_SET; publication is NEVER and atomic per PNG; the stable GUI copy becomes compatibility debt.

Result pending only this synchronized memory-closure HEAD gate: **Slice 6 RESOLVED / PROMOTION CLOSURE GATE**.

## Next journal focus — M5 Slice 7

After the Slice-6 closure HEAD is green:

1. fresh-inspect Images→PDF and bounded Files/Folders from the exact terminal `main`;
2. give Images→PDF a sequencing advantage only insofar as it can reuse canonical `ktools-images` safety/EXIF/frame policy — do not preselect without characterizing aggregate PDF semantics;
3. if Images→PDF wins, lock supported formats, ordered pages, RGB conversion, alpha→white background, multi-frame policy, singular PDF Artifact, aggregate atomic publication and NEVER/cache behavior;
4. if Files/Folders wins, lock roots, hidden/recursion, symlink/reparse behavior, deterministic ordering, permission/OSError aggregation and report semantics;
5. do not create IMAGE_SET or a generic atomic writer without new graph/domain evidence;
6. continue using exact-head hosted evidence and memory closure before moving to the next slice.

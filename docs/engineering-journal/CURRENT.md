# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 are preserved at `docs/engineering-journal/archive/2026-08-platform-foundation.md`.

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

## H-008 — One-owner capability architecture works with real product behavior
Status: **VALIDATED** — JSON split proves direct API and workflow nodes can share one implementation owner with byte-identical behavior.

## H-009 — Durable execution should be injected, not mandatory database state
Status: **VALIDATED FOR V1** — `WorkflowEngine` accepts optional RunJournal; Memory/SQLite consume the same contract.

## H-010 — Events are execution history; tables are query projections
Status: **VALIDATED FOR SQLITE V1**.

## H-011 — Interrupted must remain distinct from Failed
Status: **VALIDATED** — unfinished state is not process-death proof.

## H-012 — Durable observability needs conservative serialization
Status: **VALIDATED / SECURITY HARDENING**.

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis
Status: **VALIDATED** — RunJournal owns lifecycle truth; Diagnostics owns richer forensic/support evidence.

## H-014 — Diagnostics must be prerequisite, not cleanup
Status: **VALIDATED AS SEQUENCING RULE**.

## H-015 — Support bundles reconstruct facts, not causal certainty
Status: **VALIDATED**.

## H-016 — Crash evidence must be durable before finalization
Status: **VALIDATED FOR V1**.

## H-017 — Prior success is not reusable-result proof
Status: **REFUTED / REPLACED** — reuse requires explicit PURE policy + matching semantic signature + valid reusable outputs.

## H-018 — Size + mtime are invalidation hints, not strong content identity
Status: **VALIDATED** — SHA-256 detects same-size/restored-mtime mutation.

## H-019 — Cacheability must be capability-owned and fail-open
Status: **VALIDATED FOR M4 V1**.

## H-020 — CACHED must be a first-class lifecycle fact
Status: **VALIDATED**.

## H-021 — Real cache proof should separate pure computation from publication side effects
Status: **VALIDATED WITH JSON NODE PACK**.

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct
Status: **VALIDATED FOR V1**.

## H-023 — Restart recovery is a new run until ownership is proved
Status: **ACCEPTED SAFETY BOUNDARY**.

## H-024 — Multi-file workflows need an honest ordered type
Status: **VALIDATED IN M5 TEXT SLICE** — `FILE_SET` is preferable to smuggling an ordered Artifact sequence through JSON/ANY. Exact V1 compatibility was enough; no new collection object was required.

## H-025 — A source can be PURE while the downstream publication node is NEVER
Status: **VALIDATED IN M5 TEXT SLICE** — `files.literal` is reusable only while its FILE Artifacts remain strongly valid; `text.merge.files` still executes because publication/replacement is required behavior.

## H-026 — Green behavior tests do not prove architectural single ownership
Status: **VALIDATED / AUDIT LESSON** — integration review found duplicate `file:// URI → Path` logic across M4 and Text despite green tests. The parser was centralized in `ktools-core.local_files` and regression-tested.

## H-027 — Legacy source of truth can become characterization source before UI rewiring
Status: **ACCEPTED MIGRATION BOUNDARY** — `ktools-text` becomes the canonical evolution owner after equivalence/evidence; the old stable GUI copy may remain temporarily as explicitly frozen compatibility debt until the traditional surface is redirected.

## E-004 — Correct output-collision guard can make non-isolated smoke red
Status: **CLASSIFIED** — fix test isolation, not safety behavior.

## E-005 — GitHub Actions Node runtime warning
Status: **RESOLVED** — root Actions moved to v7 generation.

## E-006 — Artifact signature regression initially compared only post-mutation state
Status: **RESOLVED / TEST-DESIGN LESSON**.

## E-007 — Internal cache markers can collide with legitimate user JSON
Status: **RESOLVED / SERIALIZATION HARDENING**.

## E-008 — M5 RED proved the new contract boundary, not packaging failure
Status: **RESOLVED / USEFUL RED** — run `33626957901` reached installs and failed only because FILE_SET/files.literal were intentionally absent.

## E-009 — Duplicate local-file URI parser survived GREEN until integration audit
Status: **RESOLVED / REFACTOR LESSON** — centralized `path_from_file_uri` before promotion; final code candidate `dbd39a1119ce1557d802a115404f01a3f797d93e` passed run `33627879876` 5/5.

## M4 closure

M4 canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed all five hosted jobs in run `33625955613`; M4 is resolved/promoted.

## M5 Slice 1 closure candidate

Text Node Pack V1 code candidate `dbd39a1119ce1557d802a115404f01a3f797d93e` passed all five hosted jobs in run `33627879876`.

Technical acceptance is complete. Remaining gate is synchronized canonical-memory exact-head CI, PR #8 promotion/merge and post-merge `main` verification.

## Next journal focus

After Text Slice 1 promotion:

1. re-inventory low-risk legacy capability owners rather than assuming the next feature;
2. compare dependency/native coupling, side effects, Artifact shape and composability;
3. preserve one-owner direct Tool/API + workflow architecture;
4. avoid broad GUI rewrites while capability extraction is still proving boundaries;
5. if FFmpeg/FFprobe enters scope, establish the shared diagnostic subprocess boundary first.

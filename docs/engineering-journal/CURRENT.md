# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 are preserved at `docs/engineering-journal/archive/2026-08-platform-foundation.md`.

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

## H-008 — One-owner capability architecture works with real product behavior
Status: **VALIDATED** — JSON split proves direct API and workflow nodes can share one implementation owner with byte-identical behavior.

## H-009 — Durable execution should be injected, not mandatory database state
Status: **VALIDATED FOR V1** — `WorkflowEngine` accepts optional RunJournal; Memory/SQLite consume the same contract.

## H-010 — Events are execution history; tables are query projections
Status: **VALIDATED FOR SQLITE V1** — transactionally maintained projections are useful without claiming full event sourcing.

## H-011 — Interrupted must remain distinct from Failed
Status: **VALIDATED** — M2/M3/M4 all preserve the boundary; unfinished state is not process-death proof.

## H-012 — Durable observability needs conservative serialization
Status: **VALIDATED / SECURITY HARDENING** — unknown objects avoid arbitrary repr/reflection; diagnostics redacts secrets; M4 cache codec uses explicit envelopes.

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis
Status: **VALIDATED** — RunJournal owns lifecycle truth; Diagnostics owns richer forensic/support evidence.

## H-014 — Diagnostics must be prerequisite, not cleanup
Status: **VALIDATED AS SEQUENCING RULE** — future native/subprocess/integration capabilities include diagnostics in Definition of Done.

## H-015 — Support bundles reconstruct facts, not causal certainty
Status: **VALIDATED** — runtime evidence records observations; later debugging may form hypotheses.

## H-016 — Crash evidence must be durable before finalization
Status: **VALIDATED FOR V1** — append-written diagnostic evidence survives abnormal finalization boundaries conservatively.

## H-017 — Prior success is not reusable-result proof
Status: **REFUTED / REPLACED** — reuse requires explicit PURE policy + matching semantic signature + valid reusable outputs.

## H-018 — Size + mtime are invalidation hints, not strong content identity
Status: **VALIDATED** — same-size content mutation with restored mtime is detected by SHA-256.

## H-019 — Cacheability must be capability-owned and fail-open
Status: **VALIDATED FOR M4 V1** — default NEVER; explicit PURE only; cache-store failures do not become workflow failures where normal execution can proceed.

## H-020 — CACHED must be a first-class lifecycle fact
Status: **VALIDATED** — handler call-count + journal sequence prove `NODE_CACHED` without fake `NODE_STARTED`.

## H-021 — Real cache proof should separate pure computation from publication side effects
Status: **VALIDATED WITH JSON NODE PACK** — `json.split.plan` caches pure transformation; `json.split` remains NEVER and republishes files.

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct
Status: **VALIDATED FOR V1** — current run gets EXECUTED/CACHED occurrence while original Artifact provenance is preserved.

## H-023 — Restart recovery is a new run until ownership is proved
Status: **ACCEPTED SAFETY BOUNDARY** — old RUNNING work is not auto-reclaimed; RECOVERED remains gated.

## E-004 — Correct output-collision guard can make non-isolated smoke red
Status: **CLASSIFIED** — fix test isolation, not safety behavior.

## E-005 — GitHub Actions Node runtime warning
Status: **RESOLVED** — root Actions moved to v7 generation.

## E-006 — Artifact signature regression initially compared only post-mutation state
Status: **RESOLVED / TEST-DESIGN LESSON** — preserve pre-change observation when testing mutable external state.

## E-007 — Internal cache markers can collide with legitimate user JSON
Status: **RESOLVED / SERIALIZATION HARDENING** — explicit container envelopes + regression tests.

## M4 closure

M4 synchronized canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed all five hosted jobs in run `33625955613`. M4 is resolved/promoted.

## Next journal focus — M5

M5 is active in discovery/spec mode. Before implementation:

1. inventory low-risk legacy capability owners;
2. characterize behavior at the current owner boundary;
3. prefer one-input/one-output or otherwise simple deterministic file operations before native media work;
4. decide Artifact contracts explicitly rather than returning naked paths by habit;
5. classify transformation and publication separately where that yields honest PURE/NEVER semantics;
6. integrate diagnostics at file/native boundaries;
7. preserve direct Tool/API + workflow one-owner architecture;
8. if FFmpeg/FFprobe enters scope, establish the shared diagnostic subprocess boundary first.

Leading discovery candidate is legacy Markdown/TXT merge because `merge_text_files(...)` is already a bounded real behavior in the stable monolith. It must still be compared against other low-risk candidates before scope is locked.

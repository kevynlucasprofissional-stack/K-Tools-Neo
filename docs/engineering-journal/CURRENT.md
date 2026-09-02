# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 were preserved at:

`docs/engineering-journal/archive/2026-08-platform-foundation.md`

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

---

## H-008 — One-owner capability architecture works with real product behavior

Status: **VALIDATED**
Origin: OC-001 / `packages/ktools-json/`

A K-Tools capability can have one implementation owner while being consumed through direct API and workflow nodes. JSON split integration proves shared ownership and byte-identical file output under equivalent input/config.

Practical implication: future official Node Packs preserve capability semantics → shared I/O/orchestration → thin direct/UI/workflow adapters.

---

## H-009 — Durable execution should be injected, not a mandatory database dependency

Status: **VALIDATED FOR V1**
Origin: M2 Durable Execution V1

`WorkflowEngine` accepts optional `RunJournal`; Memory and SQLite implementations consume the same logical event contract. Storage-free engine usage remains valid.

---

## H-010 — Events are execution history; tables are query projections

Status: **VALIDATED FOR SQLITE V1**
Origin: M2

SQLite event writes and run/node projection updates occur transactionally per logical event. This is not yet a claim of full event sourcing.

---

## H-011 — Interrupted must remain distinct from Failed

Status: **VALIDATED FOR V1 SEMANTICS**
Origin: M2 + M3 + M4 ownership analysis

A process/session disappearing is not the same as a normal business/runtime failure. M2 preserves `INTERRUPTED`; M3 uses `ABANDONED_OR_INTERRUPTED` for stale diagnostic sessions; M4 still refuses to infer exclusive recovery ownership from unfinished state alone.

---

## H-012 — Durable observability needs a conservative serialization allow-list

Status: **VALIDATED / SECURITY HARDENING**
Origin: M2 + M3 + M4 cache codec

Unknown objects degrade to type-only metadata instead of arbitrary `repr()`/reflection. Diagnostics adds recursive credential-pattern redaction. M4 cache output serialization uses explicit container envelopes so user JSON cannot impersonate internal Artifact markers.

---

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis

Status: **VALIDATED FOR PLATFORM DIRECTION**
Origin: M3 Diagnostics + Support Bundle V1

Run Journal owns lifecycle truth; Diagnostics owns richer forensic/support evidence. They correlate through run/workflow/node identity but remain separate concerns.

---

## H-014 — Diagnostics must be a prerequisite, not a cleanup task

Status: **VALIDATED AS SEQUENCING RULE**
Origin: M3

Cache/recovery, FFmpeg, browsers, downloaders and imported applications become substantially harder to debug if diagnostic contracts are designed after failures occur.

Practical implication: significant future runtime/subprocess/integration capabilities include diagnostic integration in Definition of Done.

---

## H-015 — A support bundle should reconstruct facts but not manufacture causal certainty

Status: **VALIDATED / PRODUCT SUPPORT INVARIANT**
Origin: M3

`diagnosticHotspots` derives from recorded facts only. Plausible explanations belong in debugging analysis, not silently inside runtime evidence as causal truth.

---

## H-016 — Crash evidence must be durable before finalization

Status: **VALIDATED FOR V1**
Origin: M3 abnormal-session recovery

`diagnostics.jsonl` is append-written during execution and `session.json` begins RUNNING. A later explicit/stale recovery can preserve evidence after abnormal termination without assuming a fresh session is abandoned.

---

## H-017 — Prior success is not a reusable-result proof

Status: **REFUTED / REPLACED BY STRONGER RULE**
Origin: M4 Artifact Lifecycle + Semantic Cache

### Rejected hypothesis
A previously `SUCCEEDED` node/run can be reused directly.

### Why it failed
Prior success does not prove:

- output files still exist;
- output content is unchanged;
- node implementation version is unchanged;
- config/semantic inputs are unchanged;
- the node is side-effect free.

### Replacement rule
Reuse requires all applicable conditions:

1. explicit `CachePolicy.PURE`;
2. matching semantic signature;
3. valid reusable outputs, including strong file revalidation where applicable.

---

## H-018 — Size + mtime are useful invalidation hints, not strong content identity

Status: **VALIDATED / SECURITY-CORRECTNESS RULE**
Origin: M4

A regression test mutates file content while preserving size and restoring the exact previous mtime. SHA-256 still detects the change.

Practical implication: quick fields may reject candidates cheaply, but cannot by themselves establish strong equality for local file reuse.

---

## H-019 — Cacheability must be capability-owned and fail-open

Status: **VALIDATED FOR M4 V1**
Origin: M4

### Claim
Cache should optimize execution without becoming a hidden requirement or guessing purity.

### Evidence
- every node defaults to `NEVER`;
- only explicitly versioned `PURE` nodes participate;
- read/write/touch/invalidation failures are normalized and normal execution continues where possible;
- uncacheable output does not convert node success into workflow failure.

### Anti-repeat lesson
Do not mark a node PURE merely because its Python implementation looks deterministic. External publication or required side effects are part of semantics.

---

## H-020 — CACHED must be a first-class lifecycle fact

Status: **VALIDATED / ACCEPTED**
Origin: M4

A call-count test proves the handler is skipped on validated reuse. Journal sequence is `RUN_STARTED -> NODE_CACHED -> RUN_SUCCEEDED`, without fake `NODE_STARTED`.

Practical implication: future UI/history can display reuse directly from lifecycle truth instead of reverse-engineering it from logs.

---

## H-021 — Real product cache proof should separate pure computation from publication side effects

Status: **VALIDATED WITH OFFICIAL JSON NODE PACK**
Origin: M4

`split_json_document` was already the pure transformation owner beneath file publication. M4 exposed it as `json.split.plan` (`PURE`) rather than weakening `json.split` (`NEVER`).

Hosted workload uses 2,000 records / 8-part planning, closes and reopens SQLite cache, and proves the real pure owner executes once total across two equivalent runs.

A separate integration proves `json.literal` may be CACHED while `json.split` executes again and republishes files.

Practical implication: future Node Packs should expose pure planning/transformation boundaries separately from side-effectful publication when the product semantics naturally support that split.

---

## H-022 — Artifact occurrence provenance and cache provenance are related but distinct

Status: **VALIDATED FOR V1**
Origin: M4 Artifact Registry

`SQLiteArtifactRegistry` records the current run/node/output occurrence as `EXECUTED` or `CACHED` while preserving the original Artifact identity/provenance and historical strong snapshot.

A cached second run therefore creates a new occurrence fact without pretending that the current node produced the file anew.

---

## H-023 — Restart recovery is a new run until ownership is proved

Status: **ACCEPTED SAFETY BOUNDARY**
Origin: M4 ownership/recovery investigation

### Rejected shortcut
Treat an old `RUNNING` row as abandoned and continue it automatically.

### Why it is unsafe
Unfinished persistence alone does not prove the original process is dead or that side effects are safe to replay. Without an atomic ownership/lease contract, two processes could act on the same logical work.

### V1 rule
Restart recovery starts a new run and may reuse validated completed PURE results through semantic cache. `RECOVERED` remains gated. M2 explicit `INTERRUPTED` reconciliation remains authoritative for incomplete old runs.

---

## E-004 — A correct output-collision guard can make a non-isolated smoke look red

Status: **CLASSIFIED / TEST-HARNESS LESSON**
Origin: OC-001

Repeated JSON-split smoke reused a temp output directory and hit intentional `overwrite=False`. Fix test isolation, not safety behavior.

---

## E-005 — GitHub Actions Node 20 deprecation warning came from action runtime majors

Status: **RESOLVED / HARNESS HARDENING**
Origin: M2

Root Actions were moved to v7 generation; hosted run `33553179743` passed all jobs.

---

## E-006 — Artifact signature regression initially compared only post-mutation state

Status: **RESOLVED / TEST-DESIGN LESSON**
Origin: M4

An early regression created two Artifact objects pointing to the same path, mutated the path, and then compared both signatures. At comparison time both saw the same new content, so the test did not prove pre/post invalidation.

Fix: capture the baseline signature before mutation, then compare against a post-mutation signature.

Anti-repeat lesson: tests for mutable external state must preserve the pre-change observation, not merely preserve two references to the same mutable resource.

---

## E-007 — Internal cache markers can collide with legitimate user JSON if containers are not enveloped

Status: **RESOLVED / SERIALIZATION HARDENING**
Origin: M4

A naive tagged-dict encoding could interpret a legitimate user mapping as an internal Artifact marker. The cache codec was changed to explicit internal container envelopes and regression-tested.

---

## Next journal focus — M5 after M4 promotion gate

Do not begin M5 code until the synchronized M4 canonical-memory HEAD passes hosted CI.

Once promoted, investigate actual legacy ownership before choosing the first local Node Pack slice. Questions to answer before implementation:

1. Which small legacy capability is deterministic, useful and least coupled to the old monolith?
2. Where is its single current behavior owner and what tests can characterize it before extraction?
3. Should outputs become first-class `Artifact` objects immediately?
4. Is the operation PURE, side-effectful, or naturally separable into pure transformation + publication?
5. What diagnostics are required for its real boundary?
6. Does it need native/subprocess tooling? If FFmpeg/FFprobe is involved, create the shared process boundary first rather than embedding process calls in individual nodes.
7. How will direct Tool/API and workflow node prove one-owner behavior without duplicating implementation?

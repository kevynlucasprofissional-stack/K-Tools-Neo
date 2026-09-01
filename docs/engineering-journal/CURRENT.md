# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 were preserved at:

`docs/engineering-journal/archive/2026-08-platform-foundation.md`

This file tracks active/recent engineering knowledge that should influence the next implementation cycles.

---

## H-008 — One-owner capability architecture works with real product behavior

Status: **VALIDATED**
Origin: OC-001 / `packages/ktools-json/`

### Claim
A K-Tools capability can have one implementation owner while being consumed through a direct API and through a workflow node.

### Evidence
The JSON split milestone established a shared `writer.split_and_write -> capability.split_json_document` owner for direct and workflow routes. Integration tests verify shared ownership and byte-identical output under equivalent input/config. Hosted Windows/Linux CI passed.

### Practical implication
Future official Node Packs preserve capability semantics → shared I/O/orchestration → thin direct/UI/workflow adapters.

---

## H-009 — Durable execution should be an injected runtime concern, not a mandatory database dependency

Status: **VALIDATED FOR V1**
Origin: M2 Durable Execution V1

`WorkflowEngine` accepts an optional `RunJournal`; Memory and SQLite implementations consume the same logical event contract. Existing storage-free engine usage remains green.

### Practical implication
Future UI/cache/recovery use existing run identities rather than inventing a second execution state model.

---

## H-010 — Events are execution history; tables are query projections

Status: **VALIDATED FOR SQLITE V1**
Origin: M2

SQLite event writes and run/node projection updates occur transactionally per logical event. This is not yet a claim of full event sourcing.

---

## H-011 — Interrupted must remain distinct from Failed

Status: **VALIDATED FOR V1 SEMANTICS**
Origin: M2 + M3

A process/session disappearing is not the same as a normal business/runtime failure. M2 preserves `INTERRUPTED`; M3 similarly uses `ABANDONED_OR_INTERRUPTED` for stale diagnostic sessions that never finalized.

### Safety implication
Neither Run Journal reconciliation nor diagnostic-session recovery should infer process death merely from an unfinished record. A future lease/ownership model is still needed for stronger automatic recovery.

---

## H-012 — Durable observability needs a conservative serialization allow-list

Status: **VALIDATED / SECURITY HARDENING**
Origin: M2 + M3

Unknown objects degrade to type-only metadata instead of arbitrary `repr()`/reflection. Diagnostics adds recursive credential-pattern redaction and avoids wholesale environment-variable snapshots.

### Evidence
Regression tests seed fake secrets through object repr, structured fields, command arguments, exception messages and child-process output. Shareable outputs must not contain those seeded values.

---

## H-013 — Lifecycle history alone is insufficient for support-grade diagnosis

Status: **VALIDATED FOR PLATFORM DIRECTION**
Origin: M3 Diagnostics + Support Bundle V1

### Claim
A Run Journal can prove which run/node transitions happened, but it cannot by itself reconstruct why a complex execution behaved unexpectedly.

### Confirming evidence
The first diagnostics implementation required additional evidence classes that do not belong in run-state projections:

- stdlib operational logs;
- exceptions/tracebacks;
- decisions and concise reasons;
- metrics/quality observations;
- batch/lots and counts;
- anomalies/inconsistent results;
- subprocess command outcome, stdout/stderr, timeout and launch failure;
- human-readable report reconstruction and raw-log inventory.

### Refutation attempt
Putting all of those fields directly into Run Journal would simplify the number of abstractions, but would overload lifecycle truth with unbounded support evidence and make run state dependent on logging concerns.

### Practical implication
Keep the two injected concerns separate:

```text
RunJournal          = lifecycle truth/history
DiagnosticsSession  = forensic/support evidence
```

Correlate them through run/workflow/node IDs and attach a Journal summary to the final support report when available.

---

## H-014 — Diagnostics must be a prerequisite, not a cleanup task

Status: **VALIDATED AS SEQUENCING RULE**
Origin: project-owner support requirement + M3 implementation

### Claim
Cache/recovery, FFmpeg, browsers, downloaders and imported applications become substantially harder to debug if their diagnostic contract is designed only after real failures occur.

### Reasoning
Those future boundaries introduce long-running side effects, native processes, network/auth state and non-deterministic external behavior. The M3 common subprocess/log/report layer gives later milestones one place to record evidence.

### Practical implication
Every significant new runtime/subprocess/integration capability after M3 includes diagnostic integration in Definition of Done.

---

## H-015 — A support bundle should reconstruct facts but not manufacture causal certainty

Status: **VALIDATED / PRODUCT SUPPORT INVARIANT**
Origin: M3 report design

### Claim
The diagnostic report can identify useful failure hotspots without pretending to know a root cause that was never observed.

### Implementation
`diagnosticHotspots` is derived only from recorded WARNING/ERROR/ANOMALY facts. The Markdown/JSON reports explicitly classify these as observations, not automatic root-cause conclusions.

Domain components remain responsible for emitting explicit quality facts such as confidence below threshold, unexpected item counts, fallback/retry use or degraded output.

### Anti-repeat lesson
A plausible explanation belongs in later debugging analysis, not silently inside the runtime evidence file as if it were a fact.

---

## H-016 — Crash evidence must be durable before finalization

Status: **VALIDATED FOR V1**
Origin: M3 abnormal-session recovery

### Claim
A diagnostic system that only writes its report at normal process exit loses the most valuable evidence on hard crashes/power loss.

### Implementation
`diagnostics.jsonl` is append-written during execution and `session.json` begins as `RUNNING`. If normal finalization never occurs, a later explicit/stale recovery can preserve the last durable JSONL evidence and package the session as `ABANDONED_OR_INTERRUPTED`.

### Boundary
Staleness is not a perfect process-ownership proof. The safe default avoids fresh sessions; future leases can improve certainty.

---

## E-004 — A correct output-collision guard can make a non-isolated smoke look red

Status: **CLASSIFIED / TEST-HARNESS LESSON**
Origin: OC-001 local smoke handoff

Repeated JSON-split smoke reused a temp output directory and hit intentional `overwrite=False`. Fix test isolation, not safety behavior.

---

## E-005 — GitHub Actions Node 20 deprecation warning came from action runtime majors

Status: **RESOLVED / HARNESS HARDENING**
Origin: M2

Root Actions were moved to v7 generation; hosted run `33553179743` passed all jobs.

---

## Next journal focus — M4

After final M3 hosted closure, the next hypotheses are:

1. what makes an `Artifact` durable/valid enough to reuse after process restart;
2. what exact inputs/config/node-version identity form a safe semantic cache key;
3. how externally modified/deleted files invalidate reuse;
4. which nodes are cache-safe versus side-effectful;
5. how `CACHED` / later recovery states extend M2 lifecycle truth;
6. how M3 diagnostics explains every cache reuse/invalidation/recovery decision;
7. what ownership/lease model is necessary before automatic resume.

Do not implement broad automatic resume until these questions have executable acceptance tests.

# Engineering Journal — Current

Historical Foundation/research entries H-001..H-007 and E-001..E-003 were preserved at:

`docs/engineering-journal/archive/2026-08-platform-foundation.md`

This file tracks the currently active/recent engineering knowledge that should influence the next implementation cycles.

---

## H-008 — One-owner capability architecture works with real product behavior

Status: **VALIDATED**
Origin: OC-001 / `packages/ktools-json/`

### Claim
A K-Tools capability can have one implementation owner while being consumed through a direct API and through a workflow node.

### Evidence
The JSON split milestone established:

```text
Direct API
    \
     -> writer.split_and_write -> capability.split_json_document
    /
json.split workflow node
```

Integration tests verify both routes reference/reach the same shared owner and produce byte-identical part files for equivalent input/config. Hosted Windows/Linux CI passed the complete pack suite and workflow smoke.

### Refutation attempt
A thin workflow adapter could still accidentally become a second implementation over time. Structural tests in `ktools-json` explicitly reject split algorithms being moved into the node adapter and assert delegation to the shared owner.

### Practical implication
Future official Node Packs should use the same separation: capability semantics → shared I/O/orchestration where needed → thin direct/UI/workflow adapters.

### Evidence record
`docs/multi-agent/handoffs/OC-001-AUDIT.md`

---

## H-009 — Durable execution should be an injected runtime concern, not a mandatory database dependency

Status: **VALIDATED FOR V1**
Origin: M2 Durable Execution V1

### Claim
`WorkflowEngine` can provide durable lifecycle/history without forcing every execution to open SQLite or coupling nodes to persistence.

### Evidence
The engine accepts an optional `RunJournal`. Existing `WorkflowEngine(registry)` usage remains green. `MemoryRunJournal` captures ordered events in-memory, while `SQLiteRunJournal` persists the same logical event contract plus query projections.

Hosted M2 tests prove success/failure ordering, no-journal compatibility, SQLite close/reopen queries and a real `json.literal -> json.split` workload.

### Refutation attempt
Embedding SQLite directly in the engine would reduce interfaces initially, but would make pure tests/headless embedding depend on storage and would couple a future alternate persistence transport to execution semantics.

### Practical implication
Future UI, cache/recovery and diagnostics should consume/build on the journal/run identities rather than invent parallel run-state stores.

---

## H-010 — Events are the execution history; tables are query projections

Status: **VALIDATED FOR SQLITE V1**
Origin: M2 SQLite implementation

### Claim
The durable event stream should be the ordered logical history, while `runs` and `node_runs` are derived query-friendly projections updated in the same transaction per event.

### Evidence
`SQLiteRunJournal.record()` inserts an event and applies the corresponding projection update inside one SQLite transaction. Queries use the projections for run/node detail and the event table for ordered history.

### Refutation boundary
This is not yet full event sourcing: schema migration, replay-to-rebuild projections and distributed consumers are not implemented or claimed.

### Practical implication
M3 should extend existing run/node/artifact identities rather than create an unrelated cache-state database.

---

## H-011 — Interrupted must remain distinct from Failed

Status: **VALIDATED FOR V1 SEMANTICS**
Origin: M2 interruption design

### Claim
A process that disappears with durable `RUNNING` records must not be rewritten as a normal node/business failure.

### Evidence
`SQLiteRunJournal.reconcile_incomplete_runs()` explicitly emits `NODE_INTERRUPTED` / `RUN_INTERRUPTED` and projects status `INTERRUPTED`. Tests persist an intentionally incomplete run, reopen the database, reconcile it and verify the separate terminal state.

### Safety decision
Reconciliation is **not automatic on journal construction**. A second live process could legitimately own a RUNNING record; auto-reconciliation would create false interruption reports without a lease/ownership model.

### Practical implication
M3 restart/recovery design must introduce explicit session/ownership semantics before any automatic resume behavior.

---

## H-012 — Journal metadata needs a conservative serialization allow-list

Status: **VALIDATED / SECURITY HARDENING**
Origin: M2 JSON-safe persistence

### Claim
Durable observability must not serialize arbitrary object internals merely because a node returned a custom Python object.

### Evidence
`to_json_safe()` explicitly supports JSON-like values, K-Tools `Artifact`, enums, paths/dates and bounded metadata representations for bytes/non-finite floats. Unknown objects fall back to qualified type + `__nonSerializable__` instead of `repr`, dataclass field inspection or generic `to_dict` execution.

A regression test uses an object whose `repr()` contains a fake token and proves that token is not persisted.

### Practical implication
New durable types should be admitted through explicit K-Tools contracts, not broad reflection.

---

## E-004 — A correct output-collision guard can make a non-isolated smoke look red

Status: **CLASSIFIED / TEST-HARNESS LESSON**
Origin: OC-001 local smoke handoff

### Fingerprint
A repeated local JSON-split smoke reused `%TEMP%/oc001-split-out`; the second run hit the intentional default `overwrite=False` collision guard.

### Classification
Correct product safety behavior, stale local test state.

### Correction
Hosted CI executes in a fresh runner temp directory. Future local filesystem smokes should use unique run directories or explicit cleanup when collision behavior is not the subject under test.

### Anti-repeat lesson
Do not weaken overwrite/collision safety to make repeated smokes idempotent. Fix test isolation.

---

## E-005 — GitHub Actions Node 20 deprecation warning came from action runtime majors, not K-Tools Node target

Status: **RESOLVED / HARNESS HARDENING**
Origin: hosted M2 run `33552906228`

### Fingerprint
The runner warned that `actions/checkout@v4` and `actions/setup-python@v5` targeted deprecated Node 20 internals and were being forced onto Node 24.

### Boundary
GitHub Action implementation runtime. K-Tools Python tests and the explicit xyflow Node.js 22 job were already green.

### Correction
After checking current official Action documentation, the root workflow was moved to the v7 generation of checkout/setup-python/setup-node. Run `33553179743` on `4f1af103dff105807981f595be24cc7bf384f08c` passed all five jobs.

### Anti-repeat lesson
Runner deprecation warnings should be classified by the Action that owns the runtime. Do not change the product's supported Python/Node versions to fix an action-internal runtime warning.

---

## Next journal focus — M3

The next hypotheses must be proven rather than assumed:

1. what makes an `Artifact` durable/valid enough to reuse after process restart;
2. what exact inputs/config/node-version identity form a safe semantic cache key;
3. whether cache/recovery belongs in `ktools-core` or a dedicated execution service layer;
4. how a recovered/cached node is represented without corrupting the V1 event truth;
5. what invalidates persisted outputs when files disappear or change outside K-Tools.

Do not implement broad automatic resume until those questions have executable acceptance tests.

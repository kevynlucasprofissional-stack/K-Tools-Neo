# Tasks — Artifact Lifecycle + Recovery + Semantic Cache V1

Status legend: `[ ]` pending, `[~]` active, `[x]` complete, `[!]` blocked.

## M4-001 — Artifact strong identity

- [x] file:// snapshot model;
- [x] size + mtime quick checks;
- [x] SHA-256 strong identity;
- [x] rehash before reuse when quick fields match;
- [x] deletion/modification/change-during-observation handling;
- [x] unsupported URI/folder fail-closed semantics.

## M4-002 — Semantic node identity

- [x] CachePolicy enum;
- [x] default NEVER;
- [x] explicit PURE opt-in;
- [x] node implementation version;
- [x] deterministic canonical JSON signature;
- [x] config/input/version sensitivity;
- [x] Artifact content identity independent of random ids;
- [x] opaque/noncanonical values reject caching.

## M4-003 — Persistent semantic cache

- [x] SQLiteNodeCache;
- [x] origin run/node provenance;
- [x] safe output codec;
- [x] Artifact output snapshots;
- [x] close/reopen persistence;
- [x] last-used tracking;
- [x] invalidation;
- [x] storage failures wrapped as CacheError;
- [x] cache failures fail open at engine boundary.

## M4-004 — Cached lifecycle truth

- [x] NODE_CACHED event;
- [x] NodeRunStatus.CACHED;
- [x] SQLite projection without fake NODE_STARTED;
- [x] cached outputs preserve origin run/node evidence;
- [x] old normal execution semantics remain compatible.

## M4-005 — Engine selective reuse

- [x] optional injected NodeCache;
- [x] explicit NEVER bypass;
- [x] PURE signature lookup;
- [x] candidate metadata validation;
- [x] output Artifact revalidation;
- [x] cached output contract validation;
- [x] invalid candidate recomputation;
- [x] cache read/write/touch/invalidation diagnostics;
- [x] no false cache-miss event after cache read failure;
- [x] uncacheable output does not fail successful workflow.

## M4-006 — Artifact registry

- [x] SQLiteArtifactRegistry;
- [x] run/node/output-port/value-path provenance;
- [x] EXECUTED vs CACHED occurrence source;
- [x] historical snapshot persistence;
- [x] current validity query;
- [x] unsupported strong validity remains explicit;
- [x] engine injection;
- [x] registry failures fail open;
- [x] core/JSON CLI option.

## M4-007 — Real JSON workload

- [x] json.literal marked PURE;
- [x] json.split remains NEVER;
- [x] json.split.plan exposes pure split_json_document owner;
- [x] 2,000-record cache integration workload;
- [x] close/reopen cache reuse;
- [x] owner call count proves computation skipped;
- [x] real JSON CLI proves source CACHED while splitter still executes/publishes;
- [x] diagnostic report contains cache reuse and policy-bypass decisions.

## M4-008 — Recovery / retention boundary

- [x] define new-run cache-assisted restart recovery;
- [x] reject automatic in-flight resume without ownership evidence;
- [x] define minimum future lease/ownership requirements;
- [x] retain explicit M2 INTERRUPTED semantics;
- [x] keep RECOVERED unavailable in V1;
- [x] no automatic deletion of user files;
- [x] document metadata-only ownership of cache/registry stores.

## M4-009 — Hosted evidence and memory closure

- [x] accepted code candidate matrix green;
- [x] record representative core/JSON counts;
- [x] update spec/tasks;
- [~] update evidence/final report/ADRs/testing/journal/current state/roadmap;
- [ ] final memory-head matrix green;
- [ ] promote M5 only after final matrix.

# Final Report — M4 Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **IMPLEMENTATION RESOLVED / FINAL MEMORY-HEAD CI PENDING**

## Objective

Add a conservative reusable-execution layer to K-Tools without lying about execution history, returning stale files, or skipping required side effects.

## Initial state

Before M4:

- M2 retained durable run/node lifecycle history;
- M3 produced support-grade diagnostics;
- `Artifact` existed as a runtime model but had no strong persistent validity lifecycle;
- repeated deterministic work always recomputed;
- there was no semantic node cache;
- successful old runs could not safely be treated as reusable merely from status.

## Implemented contracts

### Artifact strong validity

Local file Artifacts can be snapshotted with size, mtime-ns and SHA-256. Reuse always revalidates the current file and rehashes when quick fields still match.

### Semantic node identity

Node definitions now declare:

- implementation `version`;
- `CachePolicy`, default NEVER;
- explicit PURE eligibility.

Semantic signatures are deterministic across run ids and sensitive to semantic config/input/version/content changes.

### Persistent node cache

`SQLiteNodeCache` persists node outputs and provenance across process boundaries. Cache is optional and fail-open.

### Explicit CACHED lifecycle

A reused node emits `NODE_CACHED` and projects `NodeRunStatus.CACHED`; no `NODE_STARTED` is fabricated.

### Artifact registry

`SQLiteArtifactRegistry` persists Artifact observations per run/node/output port/value path and records whether the current occurrence came from EXECUTED or CACHED output.

### CLI integration

Core and JSON CLIs expose:

```text
--cache <sqlite-db>
--artifact-registry <sqlite-db>
```

### Real JSON pure capability

`json.split.plan` exposes the existing pure `split_json_document` owner as a cacheable Node Pack operation. `json.split` deliberately remains NEVER because its file-publication effect must occur.

## Hypotheses and refutation results

### H1 — Previous SUCCEEDED means reusable

**Refuted.** A prior success says nothing about current file existence/content, current implementation version, changed config/input, or side-effect requirements.

Replacement rule: reuse requires explicit PURE policy + semantic signature + output validity.

### H2 — size + mtime are enough for file validity

**Refuted.** Regression changes content while restoring size and exact mtime. SHA-256 still detects the mutation.

Replacement rule: quick fields reject changes; hash establishes strong content equality.

### H3 — deterministic-looking node can be cached automatically

**Refuted as unsafe architecture.** Purity is an explicit capability contract. Default is NEVER.

### H4 — cached result can be represented as ordinary node success

**Refuted.** That would erase whether the handler actually ran.

Replacement rule: NODE_CACHED / CACHED are separate lifecycle semantics.

### H5 — cache failure should fail workflow

**Refuted.** Cache is an optimization. Read/write/touch/invalidation problems fall back to normal execution where possible and are diagnostic evidence.

### H6 — matching cache signature alone proves file output reusable

**Refuted.** Cached Artifact output may have been deleted/modified externally.

Replacement rule: output Artifact snapshots are revalidated before reuse.

### H7 — recovery requires continuing the old RUNNING row

**Refuted for V1 safety.** Exclusive ownership is not proved.

Replacement rule: M4 recovery creates a new run and may reuse validated completed PURE results. Old incomplete runs remain historical and may only be explicitly reconciled to INTERRUPTED under M2 rules.

## Significant audit fixes during implementation

- corrected a regression test that initially compared two Artifacts only after both referenced the already-mutated file;
- changed cache output serialization to container envelopes so user JSON cannot impersonate internal Artifact markers;
- required string mapping keys in signature canonicalization to prevent `1`/`"1"` collisions;
- normalized SQLite failures to CacheError so cache storage failures fail open;
- converted hashing I/O failures into explicit validity/bypass evidence;
- removed misleading double-reporting of a cache read error as an ordinary cache miss;
- kept `json.split` non-cacheable rather than weakening publication/collision semantics to make a cache demo pass.

## Real workload proof

The official JSON Node Pack now contains `json.split.plan`, delegating to the existing `split_json_document` implementation owner.

A 2,000-record, 8-part workload was executed twice with the SQLite cache closed/reopened between runs. The pure owner was called once total; the second run reused validated outputs and projected CACHED.

A separate CLI integration proves that in `json.literal -> json.split`:

- the source may be CACHED;
- the splitter still executes;
- files are republished;
- diagnostics explain both decisions.

## Artifact lifecycle proof

The Artifact registry persists historical observations and can independently revalidate the current file state later. A cached second run creates a new current-run occurrence marked CACHED without rewriting the original Artifact's production provenance.

## Hosted evidence

Accepted code SHA:

`c7ae2fa3953099d0bd9377da7c2c0195e96f6175`

GitHub Actions:

`33560041360`

Result: all five jobs passed.

Representative Ubuntu/Python 3.13:

- 63 core tests — OK;
- 64 JSON tests — OK;
- core CLI smoke — OK;
- JSON CLI smoke — OK;
- JSON artifact verification — OK;
- PowerShell diagnostic regression — OK.

## Explicit non-claims

M4 does not claim:

- automatic resume of an old in-flight process/run;
- `RECOVERED` status;
- distributed/shared cache;
- strong remote/directory Artifact validity;
- safe replay of arbitrary side effects;
- automatic user-file deletion;
- cacheability of opaque Python objects.

## Final state

The K-Tools runtime now has four complementary truth layers:

```text
WorkflowEngine
  ├─ RunJournal             -> what executed / lifecycle truth
  ├─ DiagnosticsSession     -> why / forensic support evidence
  ├─ NodeCache              -> validated reusable PURE results
  └─ ArtifactRegistry       -> persistent Artifact occurrence + validity provenance
```

These remain optional injected concerns rather than mandatory hidden globals.

## Promotion decision

Code implementation is accepted. M5 may start only after the final canonical documentation/memory HEAD passes the same hosted matrix.

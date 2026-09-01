# Evidence — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **CODE ACCEPTED / FINAL MEMORY-HEAD CI PENDING**

## Accepted code candidate

SHA:

`c7ae2fa3953099d0bd9377da7c2c0195e96f6175`

GitHub Actions run:

`33560041360`

All five jobs passed:

- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow spike / Node.js 22 — success.

Representative Ubuntu/Python 3.13 lane:

- **63 ktools-core tests — OK**;
- **64 ktools-json tests — OK**;
- core CLI smoke — OK;
- JSON workflow CLI smoke — OK;
- generated JSON artifact verification — OK;
- PowerShell diagnostic smoke inherited from M3 — OK.

## Artifact validity evidence

Core tests prove:

- SHA-256 snapshot creation for local file Artifacts;
- unchanged file validation;
- missing file invalidation;
- quick rejection when size or mtime changes;
- same-size content mutation remains detectable even when the exact prior mtime is restored;
- strong validation fails closed for folders/remote URIs;
- file changes while observation/validation are detected;
- I/O observation failures cannot become a false strong-validity claim.

Content identity excludes random Artifact/run ids.

## Semantic signature evidence

Tests prove cache signatures change when any semantic dimension changes:

- node implementation version;
- config;
- scalar/JSON input;
- Artifact content.

Equivalent JSON mappings are order-independent. Artifact objects with different random ids/provenance but identical content produce the same semantic input identity. Opaque inputs and non-string mapping keys fail closed rather than entering an ambiguous signature.

## Persistent cache evidence

`SQLiteNodeCache` tests prove:

- entries survive close/reopen;
- origin run/node provenance persists;
- last-used timestamp can be updated;
- nested JSON/container values round-trip;
- user JSON cannot collide with internal cache-envelope markers;
- opaque custom objects and raw Path outputs are not cached;
- SQLite runtime failures are normalized to CacheError;
- invalidation removes stale entries;
- Artifact outputs are rehydrated as Artifact values and retain strong validity snapshots.

## Engine reuse evidence

Call-count tests prove that a second equivalent PURE execution does not invoke the handler.

Second-run journal sequence is explicitly:

```text
RUN_STARTED
NODE_CACHED
RUN_SUCCEEDED
```

There is no fake `NODE_STARTED` for a reused node. SQLite projection status is `CACHED`.

Additional tests prove:

- config changes cause normal execution;
- NEVER always executes;
- missing cached Artifact output invalidates and recomputes;
- cache read/write failures do not fail the workflow;
- cache-ineligible output does not turn node success into workflow failure;
- cache diagnostics report concrete observed reasons.

## First-party CLI evidence

Core CLI supports:

```text
--cache <sqlite-db>
--artifact-registry <sqlite-db>
```

A regression test invokes the CLI twice with the same cache database and proves the second process/invocation projects the node as CACHED.

The JSON Node Pack CLI exposes the same options.

## Real official Node Pack evidence

### Side-effect preservation

`json.split` remains explicitly `CachePolicy.NEVER`.

A real CLI test runs the same `json.literal -> json.split` workflow twice with `overwrite=True` and persistent cache/journal:

- second-run `source` status = CACHED;
- second-run `splitter` status = SUCCEEDED;
- split output files are republished;
- output payload remains deterministic;
- diagnostic report records `validated-cache-hit` for source;
- diagnostic report records `node-policy-never` for splitter.

This proves the cache does not skip required publication side effects merely because upstream content is reusable.

### Meaningful pure workload

`json.split.plan` exposes the real pure `split_json_document` implementation owner without file I/O and is explicitly PURE.

Integration workload:

- 2,000 JSON records;
- 8-part split planning;
- first execution computes normally;
- cache database is closed;
- cache database is reopened;
- equivalent second run reuses both pure source and planner;
- patched implementation-owner call count remains **1** across both runs;
- second-run source/planner statuses are CACHED;
- second result is identical to first.

This is the M4 proof that a real product transformation—not only a fixture node—benefits from semantic reuse.

## Persistent Artifact registry evidence

`SQLiteArtifactRegistry` records occurrences tied to:

- current run;
- current node;
- output port;
- nested value path;
- EXECUTED/CACHED source;
- original Artifact id/provenance/metadata;
- strong snapshot or explicit unsupported/error evidence.

Tests prove:

- occurrence survives registry close/reopen;
- external file mutation changes current validity without erasing historical snapshot;
- nested Artifacts preserve output paths;
- unsupported remote Artifact is recorded but strong validity is `unknown`, not guessed;
- engine first run records source EXECUTED;
- equivalent cached second run records source CACHED for the same Artifact id;
- both occurrences remain bound to their current run/node/port.

## Recovery / ownership evidence boundary

M4 does not claim automatic in-flight resume.

Accepted document:

`docs/specs/artifact-recovery-cache-v1/ownership-recovery-boundary.md`

V1 restart recovery is:

> create a new run and selectively reuse completed PURE results after signature/output validity checks.

It is not:

> take an old RUNNING row and continue it automatically.

`RECOVERED` remains unavailable because exclusive process/session ownership has not yet been proved. M2 explicit `INTERRUPTED` reconciliation remains authoritative for incomplete old runs.

## Retention / file-deletion boundary

M4 cache and Artifact registry own metadata only.

- invalid cache metadata may be discarded;
- cache/registry databases may be deleted without deleting user outputs;
- M4 does not automatically remove user Artifact files;
- automatic intermediate/temp cleanup remains gated until explicit file ownership can distinguish application-owned temporary data from user results.

## Final promotion gate

The accepted code candidate is green. Canonical spec/decision/journal/current-state documents are being updated after that candidate. M4 is promoted to RESOLVED only after the final documentation/memory HEAD also passes all five hosted jobs.

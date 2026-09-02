# Evidence — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **RESOLVED / PROMOTED**

## Accepted code candidate

SHA: `c7ae2fa3953099d0bd9377da7c2c0195e96f6175`

GitHub Actions run: `33560041360`

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

Core tests prove SHA-256 snapshot creation, unchanged validation, missing-file invalidation, quick size/mtime invalidation, same-size content mutation detection with restored mtime, fail-closed unsupported URI/type handling, change-during-observation detection and hashing-I/O failure safety. Content identity excludes random Artifact/run ids.

## Semantic signature evidence

Tests prove signatures change with node implementation version, config, scalar/JSON input and Artifact content. Equivalent JSON mappings are order-independent. Artifact objects with different random ids/provenance but identical content produce the same semantic identity. Opaque inputs and non-string mapping keys fail closed.

## Persistent cache evidence

`SQLiteNodeCache` tests prove close/reopen persistence, origin run/node provenance, last-used timestamp, nested container round-trip, collision-safe internal envelopes, rejection of opaque/raw-Path outputs, CacheError normalization, invalidation and Artifact output rehydration with strong validity snapshots.

## Engine reuse evidence

Call-count tests prove a second equivalent PURE execution does not invoke the handler.

Second-run journal sequence:

```text
RUN_STARTED
NODE_CACHED
RUN_SUCCEEDED
```

There is no fake `NODE_STARTED`; SQLite projection status is `CACHED`.

Additional tests prove config changes execute normally, NEVER always executes, missing cached Artifact output recomputes, cache failures fail open, cache-ineligible output does not convert node success into failure and diagnostics record concrete reasons.

## First-party CLI evidence

Core and JSON CLIs support:

```text
--cache <sqlite-db>
--artifact-registry <sqlite-db>
```

A regression invokes the CLI twice with the same cache database and proves the second process/invocation projects the node as CACHED.

## Real official Node Pack evidence

### Side-effect preservation

`json.split` remains `CachePolicy.NEVER`.

A real CLI test runs the same `json.literal -> json.split` workflow twice with persistent cache/journal and `overwrite=True`:

- second-run `source` = CACHED;
- second-run `splitter` = SUCCEEDED;
- split output files are republished;
- output remains deterministic;
- diagnostics records `validated-cache-hit` for source;
- diagnostics records `node-policy-never` for splitter.

### Meaningful pure workload

`json.split.plan` exposes the real pure `split_json_document` implementation owner without file I/O and is explicitly PURE.

Integration workload:

- 2,000 JSON records;
- 8-part split planning;
- first execution computes;
- cache database closes and reopens;
- equivalent second run reuses pure source/planner;
- patched implementation-owner call count remains **1** across both runs;
- second-run source/planner statuses are CACHED;
- second result equals first.

## Persistent Artifact registry evidence

`SQLiteArtifactRegistry` records occurrences tied to current run/node/output port/nested value path, `EXECUTED`/`CACHED` source, original Artifact identity/provenance/metadata and strong snapshot or explicit unsupported/error evidence.

Tests prove close/reopen persistence, external mutation revalidation without erasing historical snapshot, nested paths, explicit unknown validity for unsupported remote Artifact and distinct current-run EXECUTED/CACHED occurrences for the same Artifact identity.

## Recovery / ownership evidence boundary

M4 does not claim automatic in-flight resume.

Accepted document: `docs/specs/artifact-recovery-cache-v1/ownership-recovery-boundary.md`.

V1 restart recovery is a new run plus selective reuse of completed PURE results after signature/output validity checks. It is not automatic continuation of an old RUNNING row. `RECOVERED` remains unavailable until exclusive process/session ownership is proved. M2 `INTERRUPTED` reconciliation remains authoritative for incomplete old runs.

## Retention / file-deletion boundary

M4 cache and Artifact registry own metadata only. Invalid cache metadata may be discarded; cache/registry databases may be deleted without deleting user outputs; M4 does not automatically remove user Artifact files; temp/intermediate cleanup remains gated until explicit file ownership exists.

## Canonical memory promotion evidence

The synchronized canonical-memory candidate:

`d61ddfe139855b1fe9bf310fcbcc698524f3b444`

GitHub Actions run:

`33625955613`

Result: **success**. The exact memory candidate passed the complete five-job hosted matrix.

This satisfied the final M4 promotion gate. M5 code was not started before this success.

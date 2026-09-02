# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.

Canonical sequencing guide: `docs/ROADMAP.md`.

OpenCode, Antigravity and Codex remain paused as active writers unless the project owner explicitly re-enables them.

## M0 — Platform Foundation — RESOLVED

Working runtime base:

- UI-independent `packages/ktools-core/`;
- typed node/port contracts and DAG validation/execution;
- initial Artifact model;
- headless workflow CLI;
- Windows/Linux hosted CI;
- bounded imported `xcursos-runner` and `yt-dlp-tui` subsystems.

## M1 — First official Node Pack — RESOLVED

`packages/ktools-json/` proves one capability owner shared by direct API and workflow use, with classified failures, deterministic output, collision safety and hosted evidence.

Current official JSON nodes include:

- `json.literal` — PURE;
- `json.split.plan` — PURE planning over the real `split_json_document` implementation owner;
- `json.split` — NEVER because file publication is a required side effect.

Audit: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` remains evidence that React + `@xyflow/react` is a credible editor interaction layer while `ktools-core` remains runtime truth.

## M2 — Durable Execution V1 — RESOLVED

K-Tools has an optional injected Run Journal and stdlib SQLite persistence for ordered run/node lifecycle history.

Delivered:

- run/node lifecycle events and query projections;
- explicit interruption reconciliation;
- error/output metadata;
- conservative JSON-safe serialization;
- run history/detail/event query API;
- `--journal <sqlite-db>` on core and JSON CLIs;
- real official Node Pack success/failure evidence.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

## M3 — Diagnostics, Structured Logging + Support Bundle — RESOLVED / PROMOTED

The project has a first-class diagnostic/support layer before cache/recovery, media, browser and imported-app integration work.

Spec/evidence/final report: `docs/specs/diagnostics-support-bundle-v1/`.

Working contracts include:

- structured DEBUG / INFO / WARNING / ERROR / CRITICAL events;
- LOG / DECISION / METRIC / BATCH / ANOMALY / EXCEPTION / SUBPROCESS / LIFECYCLE kinds;
- run/workflow/node/stage/batch correlation;
- stdlib Python logging bridge;
- exception traceback capture;
- recursive share-safe redaction for common credential patterns;
- subprocess command/duration/exit/stdout/stderr/timeout/launch-failure diagnostics;
- real hosted PowerShell stdout/stderr evidence;
- automatic `session.json`, `diagnostics.jsonl`, `report.json`, `report.md` and `support-bundle.zip`;
- human execution reconstruction covering steps, lots, decisions, metrics, anomalies, subprocesses, errors, outputs and Run Journal lifecycle;
- CLI diagnostics enabled by default with `--diagnostics-dir` and `--no-diagnostics`;
- Ctrl+C classified as diagnostic `INTERRUPTED`;
- conservative stale abandoned-session packaging as `ABANDONED_OR_INTERRUPTED`.

M3 final memory/documentation checkpoint `5e1e46714aaefe0827c96a415d7d58d57790a187` passed all five hosted jobs in run `33557338124`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1 — IMPLEMENTATION RESOLVED / PROMOTION HEAD CI PENDING

Spec/evidence/final report: `docs/specs/artifact-recovery-cache-v1/`.

M4 adds a conservative reusable-execution layer without treating old success as sufficient evidence for reuse.

### Artifact validity and provenance

Local file Artifacts can be observed with:

- normalized local URI/path;
- size;
- mtime-ns;
- SHA-256;
- observation timestamp.

Size/mtime are quick invalidation evidence only. When they still match, SHA-256 is recomputed before strong reuse is claimed.

`SQLiteArtifactRegistry` persists Artifact occurrences tied to:

- current run;
- current node;
- output port;
- nested output value path;
- source `EXECUTED` or `CACHED`;
- original Artifact identity/provenance/metadata;
- strong snapshot or explicit unsupported/error evidence.

The registry owns metadata only and does not delete user files.

### Semantic cache

`NodeDefinition` now has:

- implementation `version`;
- `CachePolicy.NEVER` by default;
- explicit `CachePolicy.PURE` opt-in.

A semantic cache signature depends on node type/version, canonical config and semantic inputs. Artifact inputs use content identity rather than random Artifact/run ids.

`SQLiteNodeCache` persists reusable results across process boundaries. Reuse requires both a matching signature and valid output Artifacts where applicable.

Cache is an optional injected optimization and is deliberately **fail-open**: cache read/write/touch/invalidation failure is diagnostic evidence and normal node execution remains authoritative where possible.

### Explicit lifecycle truth

A reused node records:

```text
RUN_STARTED
NODE_CACHED
RUN_SUCCEEDED
```

and projects `NodeRunStatus.CACHED`.

There is no fabricated `NODE_STARTED` for a handler that did not run.

### Real workload proof

`json.split.plan` exposes the existing pure `split_json_document` capability owner without file I/O and is explicitly PURE.

A hosted integration test uses 2,000 JSON records and 8-part planning, closes/reopens the SQLite cache, executes the equivalent workflow again, and proves the real implementation owner is called once total while the second source/planner results are CACHED.

A separate first-party CLI test proves `json.literal -> json.split` can cache the source while `json.split` executes again and republishes its files. This preserves required side effects rather than optimizing them away.

### Recovery boundary

M4 does **not** claim automatic in-flight resume.

Safe V1 restart behavior is:

```text
new run
  -> recompute semantic signatures
  -> validate completed PURE candidates
      -> valid: CACHED reuse
      -> invalid/unsupported: execute normally
```

It is not safe to take an old `RUNNING` row and continue it automatically because exclusive process/session ownership has not yet been proved.

`RECOVERED` therefore remains unavailable. M2 explicit `INTERRUPTED` reconciliation remains authoritative for abandoned in-flight history.

Accepted boundary: `docs/specs/artifact-recovery-cache-v1/ownership-recovery-boundary.md`.

### CLI surfaces

Core and JSON CLIs expose:

```text
--journal <sqlite-db>
--cache <sqlite-db>
--artifact-registry <sqlite-db>
--diagnostics-dir <dir>
--no-diagnostics
```

All persistence/diagnostic concerns remain injected/optional rather than hidden global runtime requirements.

### Accepted hosted code evidence

Accepted code candidate:

`c7ae2fa3953099d0bd9377da7c2c0195e96f6175`

GitHub Actions run:

`33560041360`

All five jobs passed. Representative Ubuntu/Python 3.13 lane executed:

- **63 ktools-core tests — OK**;
- **64 ktools-json tests — OK**;
- real PowerShell diagnostic regression — OK;
- core CLI smoke — OK;
- JSON workflow CLI smoke — OK;
- generated JSON artifact verification — OK.

The subsequent canonical ADR checkpoint `38c0dad7799334ac44477ecc5992d02e7bf46b04` also passed all five jobs in run `33560424024`.

### Current promotion gate

M4 implementation and its acceptance evidence are resolved. This document, `ROADMAP.md`, `TESTING.md` and the Engineering Journal are being synchronized into one final canonical-memory candidate.

M4 becomes **RESOLVED / PROMOTED** only after that exact memory HEAD passes the same five hosted jobs.

## Architecture direction now

The runtime has four complementary truth/optimization concerns:

```text
WorkflowEngine
  ├─ RunJournal          -> lifecycle truth/history
  ├─ DiagnosticsSession  -> forensic/support evidence
  ├─ NodeCache           -> validated reusable PURE results
  └─ ArtifactRegistry    -> persistent Artifact occurrence/validity provenance
```

Rules carried forward:

- no old `SUCCEEDED` row is sufficient for reuse;
- cacheability is explicit, never inferred;
- side effects are not skipped without a proved replay/publication contract;
- cache failure must not become workflow failure where normal execution is possible;
- `CACHED` is distinct from ordinary execution;
- unfinished state is not proof of process death;
- user output files are not automatically deleted merely because cache metadata becomes stale;
- diagnostics is part of Definition of Done for future native/subprocess/integration capabilities.

## Next exact action

Run the complete hosted matrix on the synchronized M4 memory candidate. If all five jobs are green, mark M4 promoted, move M5 to ACTIVE and select the first official local Node Pack slice from real legacy inventory before changing implementation code.

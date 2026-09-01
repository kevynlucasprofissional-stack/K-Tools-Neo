# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.

OpenCode, Antigravity and Codex are paused as active writers unless the project owner explicitly re-enables them. Prior audited work remains part of product history/evidence.

Canonical sequencing guide: `docs/ROADMAP.md`.

## M0 — Platform Foundation — RESOLVED

Working runtime base:

- `packages/ktools-core/` provides a UI-independent Python workflow runtime;
- typed node/port contracts;
- graph validation for node/port existence, required inputs, duplicate target-input connections, type compatibility and cycles;
- deterministic DAG execution;
- initial `Artifact` model;
- headless workflow CLI;
- legacy GUI and loose utilities preserved as behavior inventory;
- `apps/xcursos-runner/` and `apps/yt-dlp-tui/` preserved as bounded imported subsystems.

## M1 / OC-001 — first official Node Pack — RESOLVED

`packages/ktools-json/` owns JSON document splitting extracted from real legacy K-Tools behavior.

Verified one-owner architecture:

```text
Direct API (`ktools_json.api.split_json`)
                 \
                  -> `writer.split_and_write`
                         -> `capability.split_json_document`
                  /
Workflow node (`json.split`)
```

The pack provides classified failures, deterministic output naming, overwrite collision protection, atomic publication, post-write JSON validation, typed JSON ports and artifact-shaped output metadata.

Hosted acceptance run `33551124229` passed Ubuntu/Windows × Python 3.10/3.13 plus the xyflow spike.

Audit: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` proved React + TypeScript + `@xyflow/react` as a credible graph-interaction layer while preserving `ktools-core` as runtime authority.

Accepted directions:

- palette/library + canvas + inspector;
- compact nodes, detailed settings in the inspector;
- typed connection preflight backed later by shared runtime contracts;
- explicit MissingNode placeholder concept;
- execution state supplied by runtime events, not a frontend workflow engine.

Still unproven for production: measured large-graph performance, lossless MissingNode round-trip, complete reconnection behavior, accessibility compliance and a real cached lifecycle.

Audit: `docs/multi-agent/handoffs/AG-001-AUDIT.md`.

## M2 — Durable Execution V1 — RESOLVED

K-Tools can now retain a durable record of what happened during a workflow run.

### Runtime contract

`WorkflowEngine` accepts an optional `RunJournal`. Existing `WorkflowEngine(registry)` usage remains valid and storage-free.

Lifecycle events currently include:

- `RUN_STARTED`;
- `NODE_STARTED`;
- `NODE_SUCCEEDED`;
- `NODE_FAILED`;
- `RUN_SUCCEEDED`;
- `RUN_FAILED`;
- explicit `NODE_INTERRUPTED` / `RUN_INTERRUPTED` reconciliation events.

Accepted run/node terminal semantics in V1: `SUCCEEDED`, `FAILED`, `INTERRUPTED`; active work is `RUNNING`.

### Persistence

`SQLiteRunJournal` uses stdlib `sqlite3` and persists:

- ordered journal events;
- run projections;
- node-run projections;
- start/end timestamps;
- error type/message;
- conservative JSON-safe output metadata.

It provides run history/detail/event queries and can explicitly reconcile persisted incomplete `RUNNING` records to `INTERRUPTED` after a prior process/session disappears.

Reconciliation is deliberately opt-in; M2 does not pretend to know whether another live process still owns a run.

### Real product boundary

Both headless CLIs support:

```text
--journal <sqlite-db>
```

The real `json.literal -> json.split` Node Pack workflow is covered for durable success and durable failure, including close/reopen query evidence and generated-file validation.

### Hosted evidence

Code acceptance:

- head `74325c1445c4622383d5da061184ca2d91fde70b`;
- GitHub Actions run `33552906228`: **success**;
- representative Ubuntu/Python 3.13: **20 core tests OK + 58 JSON Node Pack tests OK**, plus both CLI smokes and artifact verification;
- all four Python matrix lanes and the xyflow job succeeded.

Harness hardening:

- GitHub Actions moved to the v7 generation of checkout/setup-python/setup-node;
- head `4f1af103dff105807981f595be24cc7bf384f08c`;
- run `33553179743`: **all five jobs success**.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

### Explicit M2 non-claims

Not implemented or claimed yet:

- automatic resume/replay;
- semantic cache;
- cancellation;
- multi-process ownership leases;
- remote/distributed workers;
- durable validity/integrity semantics for file artifacts.

Those boundaries move into M3 rather than being inferred from the existence of SQLite history.

## CI coverage now

Root workflow: `K-Tools CI`.

### Core + official JSON Node Pack matrix

Ubuntu/Windows × Python 3.10/3.13:

- editable install of `ktools-core` and `ktools-json`;
- complete core suite, including Durable Execution tests;
- complete JSON Node Pack suite, including durable real-workload tests;
- core CLI smoke;
- JSON workflow smoke;
- generated JSON artifact verification.

### xyflow spike

Ubuntu / Node.js 22:

- `npm ci`;
- build;
- lint;
- deterministic Vitest suite.

## Architecture direction accepted

- one capability / one implementation owner;
- direct Tool/API and Workflow usage share capability implementations;
- Node Packs are the reusable extension boundary;
- `ktools-core` remains workflow/runtime authority;
- Run Journal is an injected runtime contract; SQLite is one implementation, not the engine itself;
- ordered events are execution history while run/node tables are query projections in V1;
- `INTERRUPTED` is distinct from business/runtime `FAILED`;
- unknown custom output objects are not reflectively persisted by the journal;
- `@xyflow/react` remains the leading graph interaction layer, not an engine;
- imported applications are adapted before invasive rewrites.

## Active roadmap milestone — M3 Artifact Lifecycle + Recovery + Semantic Cache

Status: **ACTIVE TARGET**.

M3 must build on M2 run/node identities and answer with executable evidence:

1. what makes a file-backed output a durable reusable `Artifact` after restart;
2. what exact node/input/config/version identity forms a safe semantic cache key;
3. how externally modified/deleted files invalidate reuse;
4. which nodes are safe to cache versus side-effectful nodes that must execute;
5. how `CACHED`/later recovery states relate to the M2 event truth;
6. what process/session ownership model is required before automatic resume can be safe.

The first M3 spec should prefer deterministic JSON/file workloads and avoid jumping directly to broad automatic resume.

## Not implemented yet

- persistent first-class Artifact registry/validity records;
- semantic cache and selective re-execution;
- automatic restart/resume or leases;
- official Files/Text/Image/PDF/Media Node Packs beyond JSON;
- shared FFmpeg/FFprobe capability boundary;
- XCursos Runner / YT-DLP TUI adapters;
- backend→frontend node/catalog/config/event contract;
- production visual workflow editor;
- ready-made Tools projected from workflows;
- desktop-host selection/packaging;
- agent/natural-language workflow generation.

## Next exact action

Create and execute the M3 spec under `docs/specs/artifact-recovery-cache-v1/`. Start by formalizing durable file Artifact identity/validity and node cache eligibility/signatures, prove selective reuse on deterministic workloads, then introduce recovery semantics only after ownership/invalidation rules are evidenced.

# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.

OpenCode, Antigravity and Codex are paused as active writers unless the project owner explicitly re-enables them. Prior audited work remains part of product history/evidence.

Canonical sequencing guide: `docs/ROADMAP.md`.

## Platform Foundation — resolved

The platform foundation is promoted and remains the runtime base.

Working:

- `packages/ktools-core/` provides a UI-independent Python workflow runtime;
- typed node/port contracts;
- graph validation for node/port existence, required inputs, duplicate target-input connections, type compatibility and cycles;
- deterministic DAG execution;
- initial `Artifact` model;
- headless JSON workflow CLI;
- hosted Windows/Linux Python CI;
- legacy GUI and loose utilities preserved as behavior inventory;
- `apps/xcursos-runner/` and `apps/yt-dlp-tui/` preserved as bounded imported subsystems.

## M1 / OC-001 — first official Node Pack — RESOLVED

The first real product capability has crossed the platform boundary.

`packages/ktools-json/` is now the first official Node Pack and owns JSON document splitting extracted from existing legacy K-Tools behavior.

Verified architecture:

```text
Direct API (`ktools_json.api.split_json`)
                 \
                  -> `writer.split_and_write`
                         -> `capability.split_json_document`
                  /
Workflow node (`json.split`)
```

The direct route and workflow route therefore share the same transformation and file-publication owners rather than duplicating business logic.

The pack provides classified failures, deterministic output naming, overwrite collision protection, per-file atomic publication, post-write JSON validation, typed JSON ports and artifact-shaped output metadata.

Hosted evidence:

- implementation commit: `a41aa8beaef0d22269f9ac387c972438986902f8`;
- integrated main checkpoint: `c9cdffdc6b6502b07f3546db7e3e3fafe3407068`;
- GitHub Actions run `33551124229`: **success**;
- Ubuntu/Windows × Python 3.10/3.13 successfully installed `ktools-core` + `ktools-json`, ran both test suites, core CLI smoke, JSON workflow smoke and smoke-artifact verification;
- the xyflow spike job remained green.

Conductor audit: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` proved React + TypeScript + `@xyflow/react` as a credible graph-interaction layer while preserving `ktools-core` as runtime authority.

Accepted design directions:

- palette/library + central canvas + inspector;
- compact nodes, detailed configuration outside the node body;
- typed connection preflight in UI backed later by shared runtime contracts;
- explicit MissingNode placeholder concept;
- execution-state visualization fed later by Run Journal/runtime events;
- xyflow is interaction/editor state, not workflow truth.

Not yet proven as production claims:

- large-graph performance target;
- lossless MissingNode load/edit/save/reload round-trip;
- complete edge reconnection contract;
- browser-level accessibility compliance;
- real cached lifecycle semantics.

Audit: `docs/multi-agent/handoffs/AG-001-AUDIT.md`.

## CI coverage now

Root workflow: `K-Tools CI`.

### Core + first Node Pack matrix

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- editable install of `ktools-core`;
- editable install of `ktools-json`;
- core unit/contract tests;
- JSON pack unit/contract/integration tests;
- core CLI smoke;
- JSON workflow smoke;
- JSON smoke artifact verification.

### xyflow spike

Ubuntu / Node.js 22:

- `npm ci`;
- build;
- lint;
- deterministic Vitest suite.

## Active roadmap milestone — M2 Durable Execution V1

Status: **ACTIVE TARGET**.

The next product boundary is not another visual screen. It is a durable execution model that allows K-Tools to know what happened during a real run.

Target acceptance is defined in `docs/ROADMAP.md` and will receive its own spec under `docs/specs/durable-execution-v1/`.

Core expected outcomes:

- explicit run/node lifecycle states;
- Run Journal event model;
- SQLite persistence;
- durable run/node records;
- JSON-safe output metadata;
- run history/detail query API;
- interruption observability;
- clean event contract suitable for future UI consumption;
- instrumentation remains optional so pure/in-memory engine use stays possible.

Full automatic resume and semantic cache are intentionally deferred until the persistence/journal model is proven.

## Architecture direction accepted

- one capability / one implementation owner;
- direct Tool/API usage and Workflow usage share capability implementations;
- Node Packs are the reusable extension boundary;
- `ktools-core` remains workflow/runtime authority;
- `@xyflow/react` is the leading graph interaction layer, not an engine;
- runtime contracts must separate K-Tools semantics from xyflow-specific shapes;
- Run Journal + Artifact persistence precede broad expensive-media automation;
- imported apps are adapted before invasive rewrites;
- third-party reuse remains license/ownership-aware.

## Not implemented yet

- Durable Execution V1 / Run Journal / SQLite;
- durable Artifact lifecycle;
- restart/resume and semantic cache;
- official Files/Text/Image/PDF/Media Node Packs beyond JSON;
- shared FFmpeg/FFprobe capability boundary;
- XCursos Runner and YT-DLP TUI adapters;
- backend→frontend catalog/config/event contract;
- production visual workflow editor;
- lossless MissingNode serialization round-trip;
- ready-made Tools projected from workflows;
- desktop-host selection/packaging;
- agent/natural-language workflow generation.

## Next exact action

Create and execute the M2 spec (`docs/specs/durable-execution-v1/`), instrument `WorkflowEngine` through an optional journal/persistence boundary, prove it with success + failure using real `ktools-json` workflow execution, then close the milestone with hosted CI evidence before moving to M3.

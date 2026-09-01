# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

This roadmap defines preferred product sequencing. Repository evidence may split or reorder work; material changes must be recorded in `docs/DECISIONS.md` or the active spec.

## Product destination

K-Tools Neo becomes one integrated local-first product where:

- every reusable operation is a capability/node;
- simple ready-made Tools and visual Workflows call the same implementation owners;
- workflows are built visually from typed blocks;
- expensive/local tasks are observable, durable and recoverable;
- official Node Packs cover files, text, JSON, images, PDFs, audio, video and integrations;
- mature imported applications are exposed through adapters instead of being needlessly rewritten;
- the desktop UI is a client of stable runtime contracts, not a second engine;
- later, an AI agent can compose/validate workflows through the same node catalog humans use.

---

## M0 — Platform Foundation

Status: **RESOLVED / PROMOTED**

Delivered:

- UI-independent `ktools-core`;
- typed ports and graph validation;
- deterministic DAG execution;
- initial `Artifact` model;
- headless workflow CLI;
- Windows/Linux CI;
- architecture/research memory.

Evidence: `docs/specs/platform-foundation/`.

---

## M1 — First real Node Pack

Status: **RESOLVED**

Delivered:

- `packages/ktools-json/`;
- JSON split capability extracted from real legacy product behavior;
- direct API and `json.split` node share one implementation owner;
- classified failures, collision protection and atomic file publication;
- hosted Windows/Linux Node Pack tests + workflow smoke.

Audit: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

---

## M2 — Durable Execution V1

Status: **RESOLVED**

Delivered:

- optional `RunJournal` injection into `WorkflowEngine`;
- ordered run/node lifecycle events;
- `MemoryRunJournal` for ephemeral consumers/tests;
- stdlib SQLite persistence through `SQLiteRunJournal`;
- durable run/node projections plus ordered event history;
- success/failure/error/output metadata;
- conservative JSON-safe metadata normalization;
- explicit `RUNNING -> INTERRUPTED` reconciliation after an incomplete process/session;
- run-history/detail/event query API;
- `--journal <sqlite-db>` on core and JSON Node Pack CLIs;
- real `json.literal -> json.split` durable success/failure evidence;
- Windows/Linux hosted regression.

Accepted V1 states are `RUNNING`, `SUCCEEDED`, `FAILED`, `INTERRUPTED`. Cancellation is deliberately deferred until a real cancellation boundary exists.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

Important non-claim: M2 does **not** automatically resume interrupted work or provide semantic cache.

---

## M3 — Artifact Lifecycle + Recovery + Semantic Cache

Status: **NEXT / ACTIVE TARGET**

Build on M2 rather than inventing parallel state.

Primary questions to prove:

1. What makes a file-backed output a durable, reusable `Artifact` after process restart?
2. Which inputs/config/node identity/version form a safe semantic execution signature?
3. How are external file changes/disappearance detected before cache reuse?
4. Which outputs may be skipped/reused and which side-effect nodes must always execute?
5. What is the exact event/state distinction among normal success, cache reuse and later recovery?
6. What session/ownership boundary is needed before automatically resuming an incomplete run?

Target capabilities:

- persistent `Artifact` records with provenance (`run`, `node`, output port, URI, metadata);
- local file existence/integrity observations where applicable;
- stable workflow/node signature model for cache keys;
- selective reuse of valid prior outputs;
- invalidation when inputs/config/node version or artifact validity changes;
- safe restart/recovery semantics built on M2 run/node identities;
- explicit `CACHED` / `RECOVERED` semantics only if evidence supports them;
- cleanup/retention policy for temporary/intermediate artifacts.

M3 should begin with deterministic JSON/file workloads. Expensive media workflows are a later proof that caching provides meaningful practical savings.

---

## M4 — Official local Node Packs

Status: **PLANNED / ITERATIVE**

Migrate real legacy functionality behind one-owner capability packages. Prefer coherent domain packs over one-off files.

### Files / folders

- select/scan folder;
- list/filter files;
- sort/order;
- rename/export structure;
- copy/move with explicit collision policy.

### Text

- merge Markdown/TXT;
- transform/clean text;
- simple file→text/text→file boundaries.

### Images / PDF

- WebP→PNG and image conversions;
- images→PDF with explicit quality policy;
- PDF compression as a separate capability;
- PNG→ICO if still valuable.

### Media

Create one shared FFmpeg/FFprobe boundary first, then expose:

- extract audio from video;
- convert audio/video;
- join/split media;
- normalize/clean audio where dependency semantics are clear.

Do not copy GUI logic into nodes. Extract capability ownership once.

---

## M5 — Imported application adapters

Status: **PLANNED**

Expose mature applications as K-Tools capabilities without destroying their internal architecture.

### YT-DLP TUI adapter

- URL/playlist input;
- destination/options;
- process/run correlation;
- progress/result/artifact translation;
- preserve auth-expired/unavailable classifications.

### XCursos Runner adapter

- course/run input;
- preserve browser/session and diagnostics boundaries;
- expose output artifacts to K-Tools;
- do not duplicate downloader/navigation internals in `ktools-core`.

Adapters come before invasive forks.

---

## M6 — Runtime Contract API for UI

Status: **PLANNED**

Before production editor work, publish stable machine-readable contracts for:

- Node Pack/catalog metadata;
- node definitions and port types;
- config schema / form metadata;
- workflow serialization;
- MissingNode preservation;
- validation response;
- run/node journal events;
- artifact summaries;
- execution commands and cancellation boundary where supported.

Transport (in-process/local HTTP/IPC/etc.) should be selected from desktop-host evidence, not assumed early.

---

## M7 — Production Workflow Editor

Status: **PLANNED**

Use lessons from `spikes/xyflow-editor/`, but do not polish the spike directly into production.

Leading UI architecture:

```text
Node Library / Palette | Canvas (xyflow) | Inspector
                         ↓
                  Run / Artifacts panel
```

Required:

- real catalog from runtime contracts;
- typed connection feedback plus backend validation;
- dynamic config forms from metadata/schema;
- workflow load/save;
- lossless unknown/MissingNode round-trip;
- run state driven by journal events;
- artifacts/output inspection;
- undo/redo and reliable reconnection/deletion;
- accessibility baseline;
- measured graph performance targets.

`@xyflow/react` owns interaction mechanics only.

---

## M8 — Ready-made Tools + Templates

Status: **PLANNED**

Prove the complete product thesis:

> a workflow/capability can be projected as a simple Tool without duplicate business logic.

Targets:

- template library;
- guided forms/presets over workflows;
- “Save workflow as Tool” or equivalent manifest;
- categories/search/favorites;
- examples such as Mega Podcast, YouTube→Audio, Images→PDF and JSON Split;
- history/artifacts accessible from simple Tool runs too.

---

## M9 — Desktop Product / Packaging

Status: **PLANNED / DECISION GATED**

Choose and prove the desktop host only after runtime/UI contract needs are known.

Evaluate candidates such as Tauri/Electron against:

- Windows-first packaging;
- Python sidecar/runtime management;
- Node.js/subprocess adapters;
- filesystem dialogs and drag/drop;
- update model;
- startup time / RAM;
- code signing/installer ergonomics;
- LAN/local API implications if desired later.

The goal is one K-Tools Neo product, not a browser tab plus unrelated CLIs.

---

## M10 — Agent-first composition

Status: **LATER**

Only after node contracts, validation, persistence and observability are stable:

- machine-readable node catalog for agents;
- natural-language → workflow draft;
- explain/validate/repair graph;
- inspect available capabilities;
- generated workflows pass the same validator as human-authored workflows;
- edits remain inspectable/reversible;
- agent actions never bypass safety/overwrite/auth boundaries owned by capabilities.

---

## M11 — Release hardening

Status: **CONTINUOUS + FINAL RELEASE GATE**

Across all milestones:

- keep Windows/Linux core CI green;
- add native/runtime evidence at the boundary actually claimed;
- keep dependencies/license inventory clean;
- remove duplicate legacy ownership as capabilities migrate;
- performance/profile expensive workflows;
- structured diagnostics;
- migration/version strategy for workflow files and Node Packs;
- security review for paths, subprocesses, secrets/cookies and community plugins;
- documentation/onboarding;
- release/installer smoke on clean Windows environments.

A visually complete UI is not “top” if runtime state, recovery, error boundaries or tests are weak. K-Tools is quality-first: usability and engineering integrity advance together.

---

## Execution rule

The active implementer normally takes the **first unresolved milestone whose prerequisites are satisfied**, creates/updates an explicit spec, works through evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure, then advances to the next milestone while capacity remains.

Do not keep extending an old spec as a catch-all. Each major milestone gets its own spec/evidence area under `docs/specs/`.

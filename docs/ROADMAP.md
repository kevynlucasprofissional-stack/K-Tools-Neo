# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

This roadmap defines the preferred product sequence. It is not a promise that every item must be implemented exactly as written: repository evidence may reorder or split milestones. Any material reorder must be recorded in `docs/DECISIONS.md` or the active spec.

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

Architectural result: ADR-001/ADR-007 are now supported by real product code, not only synthetic Foundation nodes.

---

## M2 — Durable Execution V1

Status: **NEXT / ACTIVE TARGET**

Goal: make a workflow run inspectable and persist its lifecycle so the product can later support history, recovery, cache and a real editor.

Required capabilities:

1. explicit run states: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED` where supported;
2. explicit node-run states with start/end/error information;
3. append-only logical Run Journal event model;
4. SQLite persistence using Python stdlib first unless evidence requires another dependency;
5. durable workflow-run and node-run records;
6. persistence of output metadata in a JSON-safe form;
7. query/read API for run history and individual run details;
8. engine instrumentation without making persistence mandatory for pure/in-memory execution;
9. interruption semantics: a process that dies during `RUNNING` must be distinguishable from a clean failure on next inspection;
10. event/data contract designed to become the future frontend run-status source.

Non-goals for the first V1 unless evidence makes them trivial:

- full automatic resume;
- semantic cache;
- distributed execution;
- remote workers;
- background daemon/service;
- production UI.

Acceptance must include `ktools-json` as a real workload plus failure-path tests.

---

## M3 — Artifact Lifecycle + Recovery + Semantic Cache

Status: **PLANNED**

Build on M2 rather than inventing parallel state.

Targets:

- persistent `Artifact` records with provenance (`run`, `node`, output port, URI, metadata);
- local file existence/integrity observations where applicable;
- workflow/node signature model for cache keys;
- selective reuse of valid prior outputs;
- invalidation rules when inputs/config/node version change;
- safe restart/recovery semantics;
- explicit distinction between `CACHED`, `SKIPPED`, `SUCCEEDED` and `RECOVERED` if evidence supports those states;
- cleanup/retention policy for temporary/intermediate artifacts.

Use expensive media workflows later to prove that cache/recovery actually saves meaningful work.

---

## M4 — Official local Node Packs

Status: **PLANNED / ITERATIVE**

Migrate real legacy functionality behind one-owner capability packages. Prefer coherent domain packs over one-off files.

Suggested order, subject to repository evidence:

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
- auth-expired and unavailable classifications preserved.

### XCursos Runner adapter

- course/run input;
- browser/session boundary preserved;
- diagnostics correlation preserved;
- output artifacts exposed to K-Tools;
- no duplicate downloader/navigation engine in `ktools-core`.

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

The API may initially be in-process/JSON serialization. Transport (local HTTP/IPC/etc.) should be chosen based on desktop-host evidence, not assumed early.

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

Prove the full product thesis:

> a workflow/capability can be projected as a simple Tool without duplicate business logic.

Targets:

- template library;
- guided forms/presets over workflows;
- “Save workflow as Tool” or equivalent manifest;
- categories/search/favorites;
- examples such as Mega Podcast, YouTube→Audio, Images→PDF and JSON Split;
- history and artifacts accessible from simple Tool runs too.

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
- code signing and installer ergonomics;
- LAN/local API implications if desired later.

The goal is one K-Tools Neo product, not a browser tab plus unrelated CLIs.

---

## M10 — Agent-first composition

Status: **LATER**

Only after node contracts, validation, persistence and observability are stable:

- machine-readable node catalog for agents;
- natural-language → workflow draft;
- explain graph;
- validate/repair graph;
- inspect available capabilities;
- generated workflows pass the exact same validator as human-authored workflows;
- edits remain inspectable/reversible;
- agent actions never bypass safety/overwrite/auth boundaries owned by capabilities.

---

## M11 — Release hardening

Status: **CONTINUOUS + FINAL RELEASE GATE**

Across all milestones:

- keep Windows/Linux core CI green;
- add native/runtime evidence at the boundary actually claimed;
- keep dependencies/license inventory clean;
- remove duplicate legacy ownership as capabilities are migrated;
- performance/profile expensive workflows;
- structured diagnostics;
- migration/version strategy for workflow files and Node Packs;
- security review for paths, subprocesses, secrets/cookies and community plugins;
- documentation and onboarding;
- release/installer smoke on clean Windows environments.

A visually complete UI is not “top” if runtime state, recovery, error boundaries or tests are weak. K-Tools is quality-first: usability and engineering integrity advance together.

---

## Execution rule

The active implementer should normally take the **first unresolved milestone whose prerequisites are satisfied**, create/update an explicit spec, work through evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure, then move to the next milestone.

Do not keep extending an old spec as a catch-all. Each major milestone gets its own spec/evidence area under `docs/specs/`.
# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth under `docs/multi-agent/MAIN_ONLY_POLICY.md`.

Latest audited frontend-spike closure checkpoint before this state update:

- Antigravity implementation: `3ecb39416f14d5561c269f783bb73d99b80458e2`;
- CI expansion: `ec01acd4225fe79813d131b6ce1489e2c9570d93`;
- AG-001 audit record: `docs/multi-agent/handoffs/AG-001-AUDIT.md`.

## Platform Foundation — promoted

The first K-Tools Neo platform foundation is already promoted and remains the runtime base.

Working now:

- `packages/ktools-core/` provides a UI-independent workflow runtime;
- typed node/port contracts exist;
- graph validation rejects unknown nodes/ports, duplicate target-input connections, missing required inputs, incompatible types and cycles;
- deterministic DAG execution exists;
- initial `Artifact` model exists with identity/provenance fields and JSON round-trip;
- headless JSON workflow CLI exists;
- the legacy GUI and loose utilities remain available as behavior inventory for incremental migration;
- `apps/xcursos-runner/` and `apps/yt-dlp-tui/` remain imported subsystems whose internals are not owned by the platform runtime.

Foundation evidence includes the original 10 unit/contract tests, CLI smoke, and green Windows/Ubuntu Python 3.10/3.13 GitHub Actions runs.

## CI now validates two product layers

The root workflow is now `K-Tools CI`.

It validates:

### Runtime/core matrix

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- editable install;
- unit/contract tests;
- CLI smoke.

### xyflow spike

Ubuntu / Node.js 22 runs:

- `npm ci`;
- `npm run build`;
- `npm run lint`;
- `npm exec vitest -- run`.

Run `33351023146` passed all of the above.

## AG-001 — xyflow editor interaction spike

Terminal state: **CLOSED / SPIKE COMPLETE WITH EVIDENCE BOUNDARIES**.

The repository contains `spikes/xyflow-editor/` using React + TypeScript + `@xyflow/react`.

The spike directly supports these design directions:

- xyflow remains the leading canvas interaction dependency;
- workflow/runtime truth remains in `ktools-core`, not React;
- palette + canvas + inspector is the leading editor composition hypothesis;
- nodes should stay compact while detailed settings move to an inspector;
- missing/unavailable node types should be represented by a placeholder rather than silently destroyed;
- frontend connection/type feedback should consume a shared/backend-owned compatibility contract later;
- execution states should be supplied by future runtime/Run Journal events rather than produced by UI execution logic.

The Conductor audit deliberately does **not** promote these as proven production facts yet:

- 150–300 node performance guarantees;
- lossless missing-node serialization round-trip;
- complete edge-reconnection behavior;
- browser-level accessibility compliance;
- real CACHED lifecycle semantics.

See `docs/multi-agent/handoffs/AG-001-AUDIT.md` for the exact evidence boundary and reuse classification.

## OC-001 — first real capability / Node Pack

Status: **ACTIVE — OpenCode currently working**.

Core acceptance claim:

> one existing useful K-Tools capability has one implementation owner and is demonstrably reusable through both a direct invocation path and a workflow node.

OpenCode owns the backend/runtime implementation stream for this task. It must rebase/pull against current `main` before publishing because AG-001 closure and CI changes landed while OC-001 was in progress.

## Architecture direction now accepted

- one capability / one implementation owner;
- direct Tool usage and Workflow usage share capability implementations;
- `ktools-core` remains workflow/runtime authority;
- `@xyflow/react` is accepted as the leading graph interaction layer for a later production-editor spec;
- xyflow objects are presentation/editor state, not canonical workflow truth;
- a mapping/domain layer must separate K-Tools contracts from xyflow-specific shapes;
- Run Journal + Artifact persistence should precede broad production use of expensive media workflows;
- third-party source reuse must remain license/ownership-aware.

## Multi-agent operating state

- ChatGPT: Conductor / Chief Architect / Integration Engineer;
- OpenCode: Runtime / Backend Implementation Lead;
- Antigravity: Frontend / UX / Product Prototype Lead;
- Codex: intentionally excluded from the K-Tools pool for now.

The repository uses **main-only development**. Parallel work is permitted only with disjoint file/contract ownership. Before a direct-to-main push, every agent must fetch/rebase current `main`, inspect intervening changes, rerun relevant tests and never force-push over concurrent work.

## Not implemented yet

- first real capability/Node Pack proof (OC-001 still active);
- workflow/run/artifact persistence and Run Journal;
- restart/recovery and semantic cache;
- production visual workflow editor;
- real backend→frontend node catalog/schema contract;
- lossless missing-node workflow serialization;
- desktop-host selection/validation;
- XCursos Runner and YT-DLP TUI adapters;
- workflow templates replacing legacy tool screens;
- agent/natural-language workflow generation.

## Next integration decision

Do **not** start polishing the xyflow spike into a production desktop editor yet.

The next Conductor gate is OC-001. After OpenCode publishes its result, audit whether the first real capability proves the one-owner architecture. Then use the combined backend evidence + AG-001 UX evidence to specify:

1. durable execution / Run Journal / Artifact persistence;
2. the backend contract consumed by a future production editor;
3. a later production-editor spec built on xyflow without reusing spike shortcuts as runtime truth.

## Foundation terminal state

**RESOLVED / PROMOTED.**

Future product milestones use their own specs/evidence instead of extending the Foundation spec as a catch-all.

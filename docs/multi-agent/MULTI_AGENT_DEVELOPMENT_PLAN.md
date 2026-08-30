# K-Tools Neo — Multi-Agent Development Plan

Status: ACTIVE — MAIN-ONLY MODEL
Owner: ChatGPT / Conductor / Chief Architect / Integration Engineer
Implementation agents: OpenCode, Antigravity
Codex: intentionally excluded for now

## 1. Operating principle

K-Tools Neo uses one active development line: **`main`**.

We still use multiple agents, but acceleration comes from **disjoint ownership**, not from maintaining many parallel Git branches.

The goal is maximum validated throughput with minimum coordination overhead.

Canonical policy: `docs/multi-agent/MAIN_ONLY_POLICY.md`.

## 2. Roles

### ChatGPT — Conductor / Chief Architect / Integration Engineer

Owns:

- architecture and target state;
- Constitution, Constraints, Current State, Decisions, Known Issues and Testing policy;
- active specs and milestone sequencing;
- ownership boundaries between agents;
- compatibility-sensitive contracts;
- conflict arbitration;
- evidence review and memory closure;
- cross-agent integration.

### OpenCode — Runtime / Backend Implementation Lead

Primary ownership:

- `packages/ktools-core/` task-local implementation;
- first-party node packs;
- workflow execution;
- Run Journal, persistence, recovery and cache;
- filesystem/media/PDF capability extraction;
- adapters/runners for Python, Node.js and CLI boundaries;
- backend/runtime tests.

OpenCode must not independently redefine repository-wide architecture or frontend truth.

### Antigravity — Frontend / UX / Product Prototype Lead

Primary ownership:

- `spikes/xyflow-editor/` while the editor is still experimental;
- future `apps/desktop/`;
- React + TypeScript shell;
- xyflow canvas integration;
- palette, canvas, inspector, run panel and artifact views;
- interaction design/accessibility;
- frontend functional tests.

Antigravity must not become a second workflow engine. `ktools-core` remains runtime truth.

## 3. Main-only Git model

Default behavior:

```text
origin/main
    │
    ├── OpenCode clone/worktree tracking main
    ├── Antigravity clone/worktree tracking main
    └── ChatGPT/GitHub integration on main
```

No task branch is required.
No draft branch is required.
No staging PR is required.

Separate local clones/worktrees are still useful because they isolate working directories, lock files and dependencies. They should all track `main`.

Before a push, every writer must:

1. fetch `origin`;
2. pull/rebase current `main`;
3. inspect upstream changes;
4. rerun relevant tests;
5. push normally, never force-push.

## 4. Parallel ownership rules

Parallelize when paths/contracts are disjoint.

Example:

| Area | Primary writer |
|---|---|
| `packages/ktools-core/` | OpenCode |
| future `packages/node-packs/*` | OpenCode |
| `spikes/xyflow-editor/` / future `apps/desktop/` | Antigravity |
| architecture/spec/canonical coordination docs | ChatGPT |
| `.github/workflows/` | ChatGPT unless explicitly delegated |
| imported `apps/xcursos-runner/` internals | upstream/integration-controlled |
| imported `apps/yt-dlp-tui/` internals | upstream/integration-controlled |

Serialize work when two agents need the same compatibility-sensitive file or contract.

Agents must not resolve semantic conflicts by blindly choosing one side.

## 5. Handoff contract

Every handoff includes:

- task/spec ID;
- starting `main` SHA;
- resulting `main` SHA or local commit SHA if push is blocked;
- files changed;
- behavior implemented;
- tests and exact results;
- native/integration evidence where applicable;
- errors and classifications;
- Journal/known-issue impact;
- remaining risks;
- exact next action.

## 6. Quality gate without PR staging

Direct-to-main does not remove quality gates.

Use:

```text
inspect
  ↓
define evidence
  ↓
RED / failing criterion
  ↓
GREEN
  ↓
REFACTOR
  ↓
local regression
  ↓
pull --rebase origin main
  ↓
revalidate
  ↓
push main
  ↓
GitHub Actions / native evidence
  ↓
fix first evidenced failure boundary if needed
```

If `main` goes red, treat it as the current incident and restore green before starting overlapping integration work.

## 7. Current acceleration waves

### Wave 1 — First real capability + editor learning

OpenCode:

- inspect real K-Tools utilities;
- choose the strongest first capability candidate;
- prove one implementation owner shared by direct invocation and workflow node;
- add tests/evidence.

Antigravity:

- continue the xyflow editor spike already present under `spikes/xyflow-editor/`;
- validate typed handles, connections, inspector, missing nodes, states and editor ergonomics;
- keep it separate from runtime execution semantics.

ChatGPT:

- arbitrate contracts and integrate findings into specs/decisions.

These streams may run in parallel because they own different paths.

### Wave 2 — Durable execution

OpenCode:

- Run Journal;
- SQLite persistence;
- run/node lifecycle;
- Artifact persistence;
- restart/recovery;
- initial cache semantics.

Antigravity:

- consume stable run/event fixtures to design run inspector and status/progress UX.

ChatGPT:

- keep runtime/event contracts single-source and reconcile both streams.

### Wave 3 — Product integrations

OpenCode:

- `yt-dlp-tui` adapter;
- `xcursos-runner` adapter;
- selected filesystem/media/PDF node packs.

Antigravity:

- Tools surface;
- workflow execution UI;
- Inputs / Settings / Outputs inspector;
- artifacts/history.

### Wave 4 — Composition maturity

OpenCode:

- subworkflows;
- control-flow/event ports if needed;
- retry/timeout/cancellation;
- selective re-execution/cache invalidation.

Antigravity:

- subflow/group UX;
- nested workflow navigation;
- partial execution UX;
- missing-node recovery;
- templates becoming ready-made Tools.

### Wave 5 — Agent-first layer

After contracts and observability are mature:

- machine-readable node catalog;
- natural-language workflow generation;
- graph validation/repair/explanation;
- generated workflows pass the same validator as human-authored workflows.

## 8. OpenCode execution contract

OpenCode should be instructed to:

1. work from current `main`;
2. read `AGENTS.md`, `MAIN_ONLY_POLICY.md`, canonical docs and its Work Packet;
3. edit only its owned backend/runtime paths;
4. work continuously through evidence → implementation → tests;
5. pull/rebase current `main` immediately before push;
6. push directly to `main` when green and conflict-free;
7. return a precise handoff.

If an older Work Packet names a dedicated branch, ignore that branch instruction under the active main-only policy.

## 9. Antigravity execution contract

Antigravity should be instructed to:

1. work from current `main`;
2. read `AGENTS.md`, `MAIN_ONLY_POLICY.md`, canonical docs, research and its Work Packet;
3. edit only its owned frontend/spike paths;
4. preserve `ktools-core` as workflow truth;
5. pull/rebase current `main` immediately before push;
6. push directly to `main` when green and conflict-free;
7. return functional evidence and a precise handoff.

If an older Work Packet names a dedicated branch, ignore that branch instruction under the active main-only policy.

## 10. Conflict protocol

If an agent discovers current `main` changed in its owned area:

- re-read the new code;
- preserve valid upstream behavior;
- rerun its evidence;
- continue only if the ownership boundary is still clear.

If the same file/contract is being modified by another active writer, pause that overlapping change and let the Conductor serialize ownership.

Never force-push `main`.

## 11. Why this model

The previous branch-heavy process added coordination cost disproportionate to the current project size.

The new model keeps the important safety properties:

- exact-current-state reads;
- explicit ownership;
- tests;
- CI;
- evidence;
- architectural authority;
- no duplicated business logic;

while removing normal task-branch and draft-PR ceremony.

The practical rule is now:

> **One `main`, multiple disjoint writers, rebase before push, test everything that matters.**

# K-Tools Neo — Multi-Agent Development Plan

Status: ACTIVE AFTER PLATFORM FOUNDATION PROMOTION
Owner: ChatGPT / Conductor / Chief Architect / Integration Engineer
Participating implementation agents: OpenCode, Antigravity
Explicitly excluded from this project for now: Codex

## 1. Purpose

Use multiple coding agents to increase throughput without creating duplicated ownership, architectural drift, merge conflicts or competing sources of truth.

The operating model is not "three agents coding the same feature". It is a controlled pipeline where each agent owns a different workstream, produces evidence on an isolated branch, and hands work back to the Conductor for integration.

## 2. Authority model

### ChatGPT — Conductor / Chief Architect / Integration Engineer

Owns:

- repository-wide architecture and target state;
- Constitution, Constraints, Current State, Decisions, Known Issues and Testing policy;
- active milestone spec/plan/tasks;
- dependency ordering between workstreams;
- ownership boundaries;
- integration review;
- conflict resolution;
- promotion/merge decisions;
- exact-head evidence and memory closure;
- cross-agent handoffs.

ChatGPT may implement integration code or small unblockers, but should prefer delegating self-contained implementation work when this does not increase coordination cost.

Only the Conductor decides that a milestone is ready for promotion to `main`.

### OpenCode — Runtime / Backend Implementation Lead

Primary ownership:

- `packages/ktools-core/` implementation under an accepted spec;
- node-pack runtime APIs and first-party node packs;
- workflow execution, Run Journal, persistence, recovery and cache;
- filesystem/media/PDF capability extraction;
- adapters/runners for Python, Node.js and CLI boundaries;
- adapter integration with `apps/xcursos-runner` and `apps/yt-dlp-tui` without duplicating their internals;
- unit, contract, integration and performance tests for owned code.

OpenCode must not independently change architectural decisions, public node contracts or canonical project state. If implementation evidence invalidates a decision/spec, it records the evidence and stops only that invalidated task, then hands the finding to the Conductor.

### Antigravity — Frontend / UX / Product Prototype Lead

Primary ownership:

- future desktop frontend under `apps/desktop/`;
- React + TypeScript application shell;
- xyflow/React Flow canvas integration;
- node palette, canvas, inspector, run panel and artifact views;
- interaction design, keyboard/mouse behavior, selection, zoom, connection UX and accessibility;
- visual states for idle/running/success/error/cached/missing-node;
- UX prototypes for Tools vs Workflows;
- visual workflow templates and subflow authoring once contracts exist;
- frontend functional tests for owned surfaces.

Until the runtime contracts stabilize, Antigravity may build isolated prototypes against fixtures or generated contract snapshots, but prototype code is not automatically production code.

Antigravity must not become a second workflow engine. xyflow state is presentation/editor state; `ktools-core` remains workflow truth.

## 3. Non-negotiable multi-agent rules

1. `main` is the integration truth and must remain promotable.
2. No agent pushes directly to `main`.
3. Every implementation task uses an isolated branch and preferably a dedicated worktree/clone.
4. Before work, the agent reads `AGENTS.md` and the canonical docs in their required order.
5. Before a material change, the agent records the exact base SHA.
6. One implementation owner per file/contract during a parallel wave.
7. Two agents must not concurrently edit the same canonical file unless the Conductor explicitly coordinates a stacked dependency.
8. Public node type IDs, port names and workflow serialization are compatibility-sensitive contracts.
9. Imported apps under `apps/xcursos-runner` and `apps/yt-dlp-tui` retain their own internal ownership; K-Tools integrates them through adapters first.
10. A checkpoint or passing local test does not authorize merge.
11. Every PR must state what was proved, what was not proved and the evidence boundary.
12. If new evidence invalidates the plan, update the plan before continuing mechanical implementation.
13. Codex is intentionally not part of this K-Tools development pool at this time.

## 4. Branch and worktree strategy

Recommended local layout on Windows:

```text
C:\Github\K-Tools-Neo\                 main / Conductor integration checkout
C:\Github\K-Tools-Neo-opencode\        OpenCode worktree/clone
C:\Github\K-Tools-Neo-antigravity\     Antigravity worktree/clone
```

Recommended branch namespaces:

```text
opencode/<milestone>-<task>
antigravity/<milestone>-<task>
integration/<milestone>
spike/<topic>
```

Examples:

```text
opencode/node-pack-files-core
opencode/run-journal-sqlite
antigravity/workflow-canvas-spike
antigravity/run-inspector-ui
```

Do not share one working directory among interactive agents. Separate worktrees/clones reduce accidental index changes, lock files and branch switches.

## 5. Integration protocol

For independent parallel work:

```text
main@SHA
├── OpenCode branch A
└── Antigravity branch B
```

Both branches start from the same accepted baseline when possible. The Conductor reviews both independently.

If A is merged first, B must be revalidated/rebased against the new `main` before promotion.

For dependent work:

```text
main
  ↓
PR A — contract/runtime
  ↓
PR B — consumer of A
```

Prefer waiting for A's contract to stabilize. If parallelism is valuable, B may temporarily consume an explicit fixture/schema snapshot. Do not invent a competing contract.

## 6. Handoff contract

Every agent handoff must include:

- repository and branch;
- base SHA and current head SHA;
- task/spec IDs;
- files changed;
- behavior implemented;
- tests executed and exact results;
- native/integration evidence if applicable;
- errors encountered and their classification;
- Engineering Journal IDs added/affected;
- known limitations;
- compatibility risks;
- decisions requested from the Conductor;
- exact next action.

Minimum PR body template:

```text
Objective:
Spec/tasks:
Base SHA:
Head SHA:
Ownership boundary:
Implemented:
Not implemented:
Tests/evidence:
Evidence boundary:
Journal/known issues:
Risks:
Next integration action:
```

## 7. Conflict-prevention ownership map

| Area | Primary owner | Integration owner | Parallel-edit rule |
|---|---|---|---|
| `packages/ktools-core/` | OpenCode | ChatGPT | Antigravity consumes contracts; does not edit engine |
| future `packages/node-packs/*` | OpenCode | ChatGPT | one pack/task owner at a time |
| future `apps/desktop/` | Antigravity | ChatGPT | OpenCode does not edit UI unless assigned boundary adapter |
| `.github/workflows/` | ChatGPT | ChatGPT | agents may propose patches, not independently redefine gates |
| `docs/CONSTITUTION.md` | ChatGPT | ChatGPT | proposal only from implementation agents |
| `docs/DECISIONS.md` | ChatGPT | ChatGPT | implementation evidence may request ADR change |
| `docs/CURRENT_STATE.md` | ChatGPT | ChatGPT | synchronized at integration checkpoints |
| `docs/KNOWN_ISSUES.md` | ChatGPT | ChatGPT | agents may add task-local evidence via handoff |
| task-local specs/evidence | assigned agent + ChatGPT | ChatGPT | one active editor per file |
| `apps/xcursos-runner/` | upstream/subtree | ChatGPT | adapters preferred over invasive edits |
| `apps/yt-dlp-tui/` | upstream/subtree | ChatGPT | adapters preferred over invasive edits |

## 8. Acceleration plan by wave

### Wave 0 — Promote Platform Foundation

Owner: ChatGPT
Parallel agents: none modifying production code

Tasks:

- rerun exact-head root CI now that the repository/account condition materially changed;
- require Windows + Ubuntu matrix to reach checkout/install/tests/CLI;
- fix evidenced failures if any;
- audit PR #1;
- merge only after acceptance is satisfied;
- start the next milestone from the promoted `main`.

Antigravity may read/reference research during this wave but should not create production UI code against an unpromoted foundation.

### Wave 1 — Prove one real capability end-to-end

Goal: prove that one existing K-Tools capability has a single implementation usable both directly and through a workflow node.

OpenCode workstream:

- inventory low-risk real capabilities from the legacy/root utilities;
- propose the first Node Pack candidate;
- extract capability logic behind a reusable handler;
- implement typed node contract;
- add unit/contract/integration evidence;
- prove the direct API/tool path and workflow path call the same implementation.

Recommended first candidates should favor deterministic local behavior and low dependency risk. The final candidate is chosen by spec after repository inspection, not by convenience alone.

Antigravity parallel workstream — non-promotable UX spike:

- create a React + TypeScript + `@xyflow/react` canvas spike in an isolated `spike/` or Antigravity branch;
- use static fixtures representing the accepted node contract;
- prototype palette → drag node → connect typed ports → inspector;
- prototype invalid-connection feedback and missing-node placeholder;
- record UX findings/screenshots/tests;
- do not create a second runtime or persist workflow truth in frontend-only structures.

Why parallelism is safe: OpenCode owns runtime semantics while Antigravity studies interaction mechanics against fixtures. The spike informs future production UI but does not block the capability proof.

### Wave 2 — Durable execution

OpenCode primary:

- Run Journal / event model;
- SQLite persistence boundary;
- run/node status lifecycle;
- artifact persistence/provenance;
- restart/recovery semantics;
- minimal semantic cache/key design;
- tests for interrupted/restarted execution.

Antigravity parallel:

- convert validated canvas lessons into production shell only after API/schema for run events is accepted;
- build run inspector states using recorded event fixtures;
- implement progress/error/cached state visualization;
- no backend lifecycle inference in UI.

ChatGPT:

- integrate contract between Run Journal and frontend event model;
- ensure one source of truth for run state.

### Wave 3 — First product integrations

OpenCode parallelizable substreams if file ownership is disjoint:

A. `yt-dlp-tui` adapter/node pack.
B. `xcursos-runner` adapter/node pack.
C. selected media/filesystem node packs.

Do not parallelize A/B inside the same adapter/runtime files without explicit ownership separation.

Antigravity:

- Tools surface generated from/shared with capability contracts;
- workflow execution UI;
- Inputs / Settings / Outputs inspector;
- artifacts/history views.

ChatGPT:

- integration tests across Python ↔ Node.js/CLI boundaries;
- upstream-update compatibility review;
- promotion sequencing.

### Wave 4 — Composition maturity

OpenCode:

- subworkflows/subflows;
- control-flow/event ports if proven necessary;
- missing-node serialization preservation;
- retry/timeout/cancellation policies;
- cache invalidation and selective re-execution.

Antigravity:

- group/subflow creation UX;
- nested workflow navigation;
- partial execution UX;
- missing-node recovery experience;
- workflow templates becoming ready-made Tools.

### Wave 5 — Agent-first layer

Only after stable contracts, persistence and observability:

- machine-readable node catalog;
- workflow generation from natural language;
- explain/validate/repair graph operations;
- agent-created workflows must pass the same validator as human-created workflows;
- generated changes remain inspectable and reversible.

## 9. When to parallelize vs serialize

Parallelize when:

- tasks have disjoint ownership;
- one task can consume a stable published contract or fixture;
- failure in one stream does not invalidate assumptions of the other;
- merge order is known.

Serialize when:

- both agents need to edit the same contract;
- UI behavior depends on an unstable runtime lifecycle;
- persistence schema is not settled;
- an upstream integration boundary is still being discovered;
- a failed hypothesis may change the entire design.

The goal is not maximum simultaneous coding. It is maximum **validated throughput**.

## 10. Prompt contract for OpenCode

Use this structure when delegating:

```text
You are the Runtime / Backend Implementation Lead for K-Tools Neo.

Repository: kevynlucasprofissional-stack/K-Tools-Neo
Agent: OpenCode
Conductor: ChatGPT

Before changing anything:
1. fetch the exact latest main/ref instructed by the Conductor;
2. read AGENTS.md and the canonical docs in order;
3. read the active spec/plan/tasks and relevant Journal entries;
4. inspect existing code/tests at the exact base SHA;
5. do not assume chat checkpoints are current truth.

Your ownership for this task is: <paths/task>.
Do not edit: <reserved paths>.

Work continuously through the assigned task using the project playbook: inspect → define evidence → RED/criterion → GREEN → REFACTOR → regression → evidence → Journal/handoff.
Do not stop for routine approval. Stop only for a real blocker or evidence that invalidates the spec/architecture.
Do not merge to main.

At handoff provide base/head SHA, changed files, tests/evidence, Journal IDs, risks and exact next integration action.
```

## 11. Prompt contract for Antigravity

```text
You are the Frontend / UX / Product Prototype Lead for K-Tools Neo.

Repository: kevynlucasprofissional-stack/K-Tools-Neo
Agent: Antigravity
Conductor: ChatGPT

Before changing anything:
1. fetch the exact latest ref instructed by the Conductor;
2. read AGENTS.md and canonical docs in order;
3. read the workflow-platform reference study and active UI/task spec;
4. treat ktools-core contracts as authoritative; do not create a second engine.

Your ownership for this task is: <apps/desktop or spike paths>.
Do not edit: ktools-core runtime/architecture docs unless the task explicitly says so.

For UI spikes, separate hypothesis/prototype evidence from production claims. Validate interactions functionally, not only with screenshots.
Do not merge to main.

At handoff provide base/head SHA, changed files, functional tests/evidence, UX findings, contract assumptions, risks and exact next integration action.
```

## 12. Conductor integration checklist

Before merging an agent PR:

- revalidate current `main` and PR head;
- inspect all changed files and ownership boundaries;
- ensure spec/task traceability;
- confirm tests prove the claimed layer;
- distinguish mock/fixture evidence from native integration;
- inspect Journal/known issues for invalidating evidence;
- check for duplicate sources of truth;
- check compatibility-sensitive node IDs/ports/schema changes;
- rebase/update and rerun exact-head CI;
- integrate one PR at a time when merge order matters;
- synchronize canonical memory after promotion.

## 13. Immediate delegation queue after PR #1

Do not start these as production branches until Foundation is promoted unless explicitly marked spike.

1. **OpenCode / discovery + implementation:** first real capability/Node Pack milestone.
2. **Antigravity / isolated spike:** xyflow editor interaction prototype using fixture contracts.
3. **ChatGPT / architecture:** specify Run Journal, Artifact lifecycle and persistence milestone based on the first capability evidence.
4. **OpenCode / next backend milestone:** Run Journal + SQLite after its spec is accepted.
5. **Antigravity / production frontend:** begin only once runtime/event contracts needed by the UI are stable enough to consume.

This ordering keeps all three agents productive while preventing the frontend from defining backend truth and preventing backend implementation from silently changing user-facing contracts.

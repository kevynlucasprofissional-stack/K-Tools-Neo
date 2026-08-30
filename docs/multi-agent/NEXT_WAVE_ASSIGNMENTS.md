# K-Tools Neo — Next Wave Assignments

Status: READY AFTER POST-MERGE MEMORY CLOSURE
Foundation main checkpoint: `bf6b5282a3df033a1394b05215a1ed97492a73c1`
Conductor: ChatGPT
Implementation agents: OpenCode, Antigravity
Codex: intentionally not assigned to K-Tools

## Goal of the next wave

Increase validated throughput by running two deliberately disjoint workstreams in parallel:

1. **OpenCode** proves the first real K-Tools capability behind a reusable node/runtime contract.
2. **Antigravity** explores the visual workflow interaction model with xyflow using fixtures, without becoming a second workflow engine or blocking backend work.

ChatGPT remains responsible for the active spec, contract arbitration, integration order, final review and promotion.

---

# Workstream OC-001 — First Real Capability / Node Pack

Agent: OpenCode
Role: Runtime / Backend Implementation Lead
Recommended branch: `opencode/first-real-node-pack`
Base: latest accepted `main` after post-merge memory closure
Promotion target: `main` through PR only

## Objective

Prove the central K-Tools architecture with production behavior:

> one existing useful K-Tools capability has one implementation owner and can be invoked both directly and as a workflow node without duplicated business logic.

## Ownership

OpenCode may own task-local runtime/node-pack files and tests assigned by the active spec.

Reserved / do not change without Conductor approval:

- `docs/CONSTITUTION.md`;
- `docs/DECISIONS.md`;
- `docs/CURRENT_STATE.md`;
- `docs/TESTING.md`;
- `.github/workflows/`;
- future `apps/desktop/`;
- internals of `apps/xcursos-runner/` and `apps/yt-dlp-tui/` unless a separate adapter task explicitly requires it.

## Required discovery before choosing the capability

Inspect the existing root utilities and legacy GUI on the exact base SHA. Rank real candidate capabilities using at least:

- actual current usefulness;
- determinism;
- low side-effect risk;
- testability;
- dependency complexity;
- degree of GUI entanglement;
- suitability for typed inputs/outputs;
- reuse value in future workflows;
- ability to prove direct path and workflow path share the same implementation.

Do not select a candidate merely because it is easiest to code.

## Preferred candidate profile

For the first proof, prefer a local, deterministic transformation that:

- already exists in K-Tools or its utilities;
- does not require authentication/network state;
- has an observable output artifact or deterministic value;
- can be tested in temporary directories;
- is useful as a building block for later audio/video/PDF workflows.

## Expected implementation shape

The active spec may refine names, but the architectural shape should be:

```text
Capability implementation
        │
        ├── direct callable/tool path
        │
        └── NodeDefinition + handler adapter
                       │
                       ▼
                 WorkflowEngine
```

There must not be a separate "workflow implementation" of the capability.

## Acceptance criteria

At minimum:

1. capability choice is justified from repository evidence;
2. one implementation owner is identifiable in code;
3. direct invocation test passes;
4. workflow-node invocation test passes;
5. both routes exercise the same core implementation;
6. typed input/output contract is validated;
7. failure behavior is explicit and correlated to the node/task boundary;
8. tests do not require modifying real user files;
9. existing Foundation tests remain green;
10. no legacy behavior is removed before equivalent functionality is evidenced;
11. handoff includes exact base/head SHA and evidence boundary.

## Evidence ladder

Expected:

- unit tests for extracted capability logic;
- contract tests for node ports/config;
- integration test through `WorkflowEngine`;
- direct-path test proving shared implementation;
- native smoke if the capability crosses FFmpeg/filesystem/other real runtime boundary;
- full existing `ktools-core` regression suite.

## Handoff format

Return:

- candidate ranking and selected capability;
- base SHA / head SHA;
- changed files;
- implementation ownership diagram;
- tests and exact results;
- native boundary evidence if applicable;
- assumptions/refutations;
- Journal IDs / known issues;
- risks;
- exact next integration action.

## Prompt ready for OpenCode

```text
You are the Runtime / Backend Implementation Lead for K-Tools Neo.

Repository: kevynlucasprofissional-stack/K-Tools-Neo
Conductor: ChatGPT
Task: OC-001 — First Real Capability / Node Pack
Recommended branch: opencode/first-real-node-pack

Before changing anything:
1. fetch the latest main and record its exact SHA;
2. read AGENTS.md and the canonical docs in their required order;
3. read docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md;
4. read docs/multi-agent/NEXT_WAVE_ASSIGNMENTS.md;
5. inspect the legacy/root utilities and relevant tests at the exact ref;
6. treat code/runtime on that ref as current-state truth.

First rank real capability candidates by usefulness, determinism, side-effect risk, testability, dependency complexity, GUI entanglement, typed-contract suitability and future workflow reuse.

Then continue automatically into the best-supported first capability unless repository evidence exposes a material architectural ambiguity that the active spec cannot resolve.

Architectural invariant: one capability / one implementation owner. Direct usage and workflow-node usage must call the same capability implementation. Do not add product behavior to the legacy monolith merely to make the workflow work.

Use the project playbook continuously: inspect → hypothesis/evidence → define proof → RED/criterion → GREEN → REFACTOR → regression → integration evidence → Journal/handoff.

Do not merge to main. Do not change canonical architecture decisions unilaterally. If evidence invalidates a decision/spec, record the evidence and hand it to the Conductor instead of silently changing the contract.

At handoff provide base/head SHA, candidate ranking, selected capability, changed files, proof that direct+workflow routes share implementation, tests/evidence, Journal IDs, risks and exact next action.
```

---

# Workstream AG-001 — xyflow Workflow Editor Interaction Spike

Agent: Antigravity
Role: Frontend / UX / Product Prototype Lead
Recommended branch: `antigravity/xyflow-editor-spike`
Base: latest accepted `main` after post-merge memory closure
Status: isolated spike; not automatically production-promotable

## Objective

Validate the interaction model for a future K-Tools workflow editor without defining backend truth.

The spike should answer whether React + TypeScript + `@xyflow/react` can provide a high-quality local workflow canvas for K-Tools concepts.

## Ownership

Preferred spike path:

```text
spikes/xyflow-editor/
```

or another path explicitly approved by the Conductor.

Do not modify:

- `packages/ktools-core/` runtime semantics;
- canonical node type compatibility rules;
- `docs/CONSTITUTION.md` or `docs/DECISIONS.md` directly;
- imported app internals.

If frontend needs a missing contract, record the requirement instead of inventing a competing backend model.

## Fixture contract

Use small fixture nodes modeled after accepted Foundation concepts, for example:

- text literal;
- text concat;
- file-like typed output;
- intentionally incompatible port;
- missing/unknown node placeholder.

Fixtures are UX test data, not a second source of workflow truth.

## UX questions to validate

At minimum:

1. palette/search → add node;
2. drag/move/select/multi-select;
3. typed input/output handles;
4. valid connection feedback;
5. invalid connection rejection/feedback;
6. reconnect/delete edge;
7. inspector for node config;
8. fit view/zoom/pan;
9. node state rendering: idle/running/success/error/cached;
10. missing-node placeholder that preserves unknown serialized data conceptually;
11. keyboard accessibility basics;
12. behavior with a moderately sized synthetic graph.

## Acceptance criteria for the spike

1. React + TypeScript project builds reproducibly;
2. `@xyflow/react` is the graph-interaction dependency;
3. no workflow execution engine is implemented in the frontend;
4. graph fixtures can be loaded and edited;
5. valid/invalid connections are demonstrated functionally;
6. inspector edits fixture config without owning runtime semantics;
7. missing-node UX is demonstrated;
8. at least one functional UI test or deterministic interaction test exists; screenshots alone are insufficient;
9. findings distinguish library limitations from K-Tools design choices;
10. handoff includes what should be reused in production and what should be discarded.

## Non-goals

- production desktop host choice;
- persistence;
- real workflow execution;
- final design system;
- backend API invention;
- merging the spike as the production editor without a subsequent production spec.

## Handoff format

Return:

- base/head SHA;
- spike path/files;
- dependency versions;
- interaction behaviors validated;
- functional test evidence;
- screenshots/video only as supplemental evidence;
- performance observations for synthetic graph size used;
- assumptions about runtime contracts;
- blockers/limitations in xyflow;
- recommendations for production editor architecture;
- exact next action.

## Prompt ready for Antigravity

```text
You are the Frontend / UX / Product Prototype Lead for K-Tools Neo.

Repository: kevynlucasprofissional-stack/K-Tools-Neo
Conductor: ChatGPT
Task: AG-001 — xyflow Workflow Editor Interaction Spike
Recommended branch: antigravity/xyflow-editor-spike

Before changing anything:
1. fetch the latest main and record the exact SHA;
2. read AGENTS.md and canonical docs in order;
3. read docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md;
4. read docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md;
5. read docs/multi-agent/NEXT_WAVE_ASSIGNMENTS.md;
6. treat ktools-core contracts as authoritative.

Create an isolated React + TypeScript + @xyflow/react interaction spike. Use fixtures representing accepted K-Tools node/port concepts. Do not implement workflow execution in the frontend and do not make xyflow the owner of workflow semantics.

Validate palette/add, move/select, typed handles, valid/invalid connection behavior, reconnection, inspector edits, viewport behavior, execution-state visuals, missing-node placeholder, keyboard basics and a moderately sized synthetic graph.

Provide functional/deterministic UI evidence; screenshots are supplemental only. Clearly separate spike findings from production claims.

Do not merge to main. At handoff provide base/head SHA, files, tests/evidence, contract assumptions, xyflow limitations, UX recommendations and exact next integration action.
```

---

# Conductor Workstream C-001 — Next Milestone Specification and Integration

Owner: ChatGPT

## Responsibilities during OC-001 + AG-001

- verify post-merge `main` checkpoint before delegating;
- create/maintain the active spec for the first real capability proof;
- prevent OpenCode and Antigravity from editing overlapping contract files;
- review OpenCode candidate ranking before treating its choice as durable architecture if evidence exposes competing high-value candidates;
- treat Antigravity output as a spike until a production UI spec adopts validated findings;
- integrate backend PR first when frontend production work depends on its contracts;
- use the first real capability evidence to specify Run Journal / Artifact persistence rather than designing durable execution entirely in the abstract.

## Intended merge order

```text
Foundation promoted
      ↓
OC-001 real capability proof ───────────────┐
                                            ├─ Conductor synthesis
AG-001 isolated UX spike (parallel) ────────┘
      ↓
Run Journal / persistence spec
      ↓
production desktop/editor spec
```

The spike may finish before OC-001, but it does not redefine the backend contract or force production UI merge order.

# AG-001 — xyflow Workflow Editor Interaction Spike

Status: READY FOR EXECUTION
Assigned agent: Antigravity
Role: Frontend / UX / Product Prototype Lead
Working branch: `agent-antigravity/xyflow-editor-spike`
Integration target: **no automatic production merge**; spike findings are reviewed by the Conductor first
Issue mirror: GitHub Issue #4 (optional; this file is sufficient even when Issues are unavailable)
Conductor: ChatGPT / Chief Architect / Integration Engineer

> This file is the authoritative task-local instruction for Antigravity. Do **not** depend on GitHub Issues being available. Everything required to start, execute, validate and hand off AG-001 is contained here together with the repository's canonical engineering documents.

---

## 1. Mission

Validate whether **React + TypeScript + `@xyflow/react`** provides the interaction model required for the future K-Tools Neo workflow editor while preserving the core architectural invariant:

> the frontend is an editor/client of workflow contracts — it is **not** the workflow engine.

This is a controlled UX/interaction spike, not permission to ship the production editor or redefine backend semantics.

The spike should answer with evidence:

- can xyflow support the canvas interactions K-Tools needs?
- can we represent typed handles and connection feedback cleanly?
- can node configuration live in an inspector instead of hard-coding behavior into node components?
- can missing/unknown nodes be preserved rather than destroyed?
- can execution states be visualized without implementing execution in the frontend?
- what parts of the spike are production-reusable and what should be discarded?

---

## 2. Mandatory read-before-work order

Before modifying code, read on the exact working ref:

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/CONSTITUTION.md`
4. `docs/CONSTRAINTS.md`
5. `docs/CURRENT_STATE.md`
6. `docs/DECISIONS.md`
7. `docs/KNOWN_ISSUES.md`
8. `docs/TESTING.md`
9. `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`
10. `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md`
11. `docs/multi-agent/NEXT_WAVE_ASSIGNMENTS.md`
12. this file
13. relevant Foundation models under `packages/ktools-core/`
14. `docs/engineering-journal/CURRENT.md`

Treat current repository code/contracts as evidence. Do not invent a frontend-only contract that contradicts the Foundation merely because it is convenient for a demo.

---

## 3. Context that must remain true

The Platform Foundation already establishes:

- a UI-independent workflow runtime;
- typed node/port definitions;
- workflow definitions and edges;
- graph validation;
- initial `Artifact` concepts;
- CLI/headless execution;
- a strategic decision that `@xyflow/react` is the leading canvas implementation candidate, while `ktools-core` remains authoritative for workflow/runtime semantics.

Your spike should test that decision, not assume it is correct without evidence.

---

## 4. Isolation requirement

Prefer an isolated path such as:

```text
spikes/xyflow-editor/
```

or another clearly spike-scoped frontend directory if repository evidence justifies it.

The spike must not silently become the production desktop app.

Do not place experimental UX logic inside `packages/ktools-core/`.

Do not couple the backend package to React/xyflow.

---

## 5. Required fixture model

Use frontend fixtures that represent accepted Foundation concepts without pretending those fixtures are workflow truth.

At minimum create fixtures for:

1. a text-literal node;
2. a text-concat/transform node;
3. a file-like typed output;
4. an input that accepts a file-like type;
5. an intentionally incompatible port pair;
6. a node with editable config;
7. an unknown/missing node placeholder preserving original unknown data;
8. execution-state metadata for idle/running/success/error/cached visualization.

The fixture layer should be easy to replace later with a real typed API/serialization adapter.

Avoid embedding execution algorithms into fixtures.

---

## 6. Interaction requirements

Functionally validate the following behaviors.

### Canvas / navigation

- pan;
- zoom;
- fit view;
- move node;
- select node;
- multi-select;
- delete selection;
- reasonable large-canvas behavior.

### Palette / node creation

- visible node palette or searchable add-node flow;
- add a fixture node to the canvas;
- categories or grouping sufficient to test future K-Tools discoverability.

### Connections

- typed input/output handles;
- create valid connection;
- reject or visibly flag invalid connection;
- reconnect edge;
- delete edge;
- avoid accidental cycles if the frontend can cheaply preflight them, but do not treat frontend checks as authoritative backend validation.

### Inspector

- selecting a node opens/shows its editable configuration;
- editing config updates the fixture graph state;
- configuration UI is derived from fixture metadata where practical rather than hard-coded per node.

### Node state visualization

Demonstrate distinct visual/semantic states for:

- idle;
- running;
- success;
- error;
- cached.

These are display states supplied by fixture data. The frontend must not execute workflow nodes merely to produce them.

### Missing node preservation

Implement a placeholder pattern for unknown node types.

The placeholder must conceptually preserve:

- original node type identifier;
- original config payload;
- original ports/serialized data where available;
- node position/identity.

The UI should clearly indicate that the required Node Pack/type is unavailable.

Do not delete or coerce unknown node data just to render the graph.

### Keyboard/accessibility basics

At minimum assess:

- keyboard deletion;
- focus visibility;
- meaningful controls/labels for critical actions;
- whether common interactions are possible without precision-only mouse behavior.

Document limitations honestly.

---

## 7. Architectural rules

These rules are mandatory:

### A. No second workflow engine

The frontend may:

- manage editable graph presentation state;
- perform UX-level prevalidation;
- show typed compatibility feedback;
- serialize fixture graph data;
- show execution status supplied by fixtures.

The frontend may **not** become the authority for:

- workflow execution ordering;
- production DAG validation;
- retry semantics;
- artifact lifecycle;
- cache semantics;
- durable execution;
- node business logic.

### B. xyflow owns interaction mechanics, not K-Tools semantics

Use `@xyflow/react` for things it is good at:

- viewport;
- nodes/edges rendering;
- handles;
- connection gestures;
- selection;
- reconnection;
- minimap if useful;
- graph UI utilities.

Keep K-Tools-specific concepts in our adapter/domain layer.

Do not encode product semantics directly into xyflow-specific object shapes if a small mapping layer can preserve independence.

### C. No premature desktop-host decision

This spike must not decide Electron/Tauri/other host unless a tiny packaging experiment is necessary to answer a concrete blocking question and the scope is explicitly documented.

The primary goal is editor interaction architecture.

---

## 8. Suggested project shape

A reasonable spike shape is:

```text
spikes/xyflow-editor/
  package.json
  src/
    app/
    domain/
      fixture-workflow.ts
      type-compatibility.ts
      execution-state.ts
    canvas/
      WorkflowCanvas.tsx
      nodeTypes/
      edgeTypes/
    palette/
    inspector/
    fixtures/
    tests/
```

This is illustrative, not mandatory. Prefer a clean separation among:

- K-Tools-like domain fixtures;
- xyflow mapping/rendering;
- interaction components;
- tests.

---

## 9. Evidence-first implementation loop

Follow the project's quality-first loop.

### Phase A — Define proof

Before implementation, define how each key hypothesis will be proven.

Examples:

- valid connection can be created;
- incompatible connection is prevented/flagged;
- unknown node survives load-edit-serialize cycle;
- config editing changes graph state without implementing execution;
- 100–300 synthetic nodes remain interactable enough for a spike-level observation.

### Phase B — RED / failing criterion

Create deterministic tests or explicit unmet scenarios.

### Phase C — GREEN

Implement the smallest coherent spike satisfying those scenarios.

### Phase D — REFACTOR

Separate xyflow mechanics from K-Tools domain fixture semantics.

### Phase E — evaluation

Run functional tests and record interaction/performance observations.

Screenshots are useful supplemental evidence but cannot be the sole proof.

---

## 10. Required testing

At least one deterministic functional/interaction test must exist, but the target is broader coverage of the highest-risk behaviors.

Prefer tests for:

- adding a node;
- valid connection;
- invalid connection rejection/feedback;
- inspector config update;
- missing-node preservation through serialization or state transformation;
- execution-state rendering mapping.

If browser/E2E tooling is practical in the spike, use it for at least the most important end-to-end canvas behavior. If it is disproportionate, use component/integration tests and clearly document the untested browser boundary.

Do not declare a behavior validated solely because the code path exists.

---

## 11. Performance observation

Create a synthetic graph large enough to expose obvious interaction problems.

Suggested observation bands:

- ~50 nodes;
- ~150 nodes;
- ~300 nodes if practical.

Record qualitatively and, where easy, quantitatively:

- initial render behavior;
- pan/zoom responsiveness;
- node dragging;
- selection;
- obvious memory/CPU issues;
- whether custom node richness causes visible degradation.

This is not a formal benchmark unless you build one. Label observations accurately.

---

## 12. Design/UX questions to answer

Your handoff must explicitly answer:

1. Should K-Tools use handles on both sides, dynamic handles, or a more constrained layout?
2. How should data types be communicated visually without overwhelming basic users?
3. What should an invalid connection look/feel like?
4. How should running/progress/error/cached state appear on a node?
5. Should detailed input/output data live on the node, inspector, bottom panel, or a combination?
6. How should missing Node Packs be presented?
7. Which interactions from n8n/ComfyUI/Node-RED style editors are worth adopting, and which create unnecessary complexity for K-Tools?
8. What is the minimum viable canvas for a first production editor?
9. What parts of the spike are implementation-quality and what parts are throwaway exploration?

Ground answers in what you actually built/tested.

---

## 13. Ownership boundaries

You primarily own the isolated frontend spike path and its tests.

Do **not** independently modify:

- `packages/ktools-core/` runtime semantics;
- `docs/CONSTITUTION.md`;
- `docs/DECISIONS.md` as architectural authority;
- root CI policy unless the spike requires an isolated job and the Conductor approves adoption;
- imported XCursos/YT-DLP internals;
- the legacy GUI in order to make the spike look integrated.

If you discover that a backend contract is insufficient, document the exact deficiency and propose a contract change in the handoff. Do not silently invent an incompatible frontend contract.

---

## 14. Dependency/licensing constraints

The expected graph library is:

`@xyflow/react`

Record the exact version used.

Before adding any additional significant library:

- identify why it is necessary;
- check its license;
- avoid bringing n8n or ComfyUI source into the spike;
- use the repository research document for donor/clean-room boundaries.

n8n and ComfyUI are references for UX/concepts under the current strategy, not general donor-code pools.

---

## 15. Git / branch discipline

Work only on:

`agent-antigravity/xyflow-editor-spike`

Before substantive changes:

- fetch current repository state;
- confirm branch and exact base;
- compare against current `main`;
- if `main` moved materially, update/rebase safely or record the divergence.

Do not write directly to `main`.

Do not merge your own PR.

Because this is a spike, opening a PR is useful for review/evidence but the PR should be clearly marked as **spike / not automatically production-promotable**.

---

## 16. Definition of Done

AG-001 reaches `SPIKE COMPLETE / READY FOR CONDUCTOR SYNTHESIS` only when:

- [ ] React + TypeScript spike builds reproducibly;
- [ ] exact `@xyflow/react` version is recorded;
- [ ] fixture/domain layer is separated from xyflow rendering mechanics;
- [ ] palette/add-node flow works;
- [ ] move/select/multi-select works;
- [ ] typed handles are demonstrated;
- [ ] valid connection works;
- [ ] invalid connection behavior is demonstrated;
- [ ] edge reconnection/deletion is demonstrated;
- [ ] inspector config editing works;
- [ ] pan/zoom/fit works;
- [ ] idle/running/success/error/cached states are represented;
- [ ] missing-node placeholder preserves unknown data conceptually and functionally;
- [ ] keyboard/accessibility basics are assessed;
- [ ] synthetic graph performance observations are recorded;
- [ ] at least one deterministic functional test exists, preferably several;
- [ ] no workflow execution engine has been created in frontend code;
- [ ] handoff distinguishes reusable production code from throwaway spike code;
- [ ] branch is pushed and review surface exists.

---

## 17. Required handoff report

At completion provide:

### Identity

- task: `AG-001`;
- branch;
- base SHA;
- head SHA;
- PR link/number if created.

### Stack

- React version;
- TypeScript version;
- `@xyflow/react` version;
- testing tools;
- any other material dependencies with licenses/reasons.

### What was built

- files/modules;
- interaction architecture;
- domain-fixture → xyflow mapping approach;
- inspector approach;
- missing-node approach;
- execution-state visualization approach.

### Evidence

- build command/result;
- tests and results;
- functional interaction evidence;
- synthetic graph observations;
- screenshots/video only as supplemental evidence if available.

### Findings

- xyflow strengths;
- xyflow limitations;
- K-Tools-specific design choices;
- backend contract assumptions/deficiencies discovered;
- accessibility issues;
- performance concerns.

### Reuse classification

For each significant module or concept state:

- reuse in production as-is;
- reuse after refactor;
- concept only;
- discard.

### Exact next action

Tell the Conductor what should be adopted into a future production-editor spec and what should explicitly not be promoted.

---

## 18. Execution prompt embedded in this file

If you are Antigravity and were only told to read this file, treat the following as your direct instruction:

> Act as the Frontend / UX / Product Prototype Lead for K-Tools Neo. Execute AG-001 completely on branch `agent-antigravity/xyflow-editor-spike`. Follow `AGENTS.md`, the canonical engineering documents, the workflow-platform research, the playbook and this Work Packet. Build an isolated React + TypeScript + `@xyflow/react` interaction spike that validates the future workflow-editor UX without creating a second workflow engine or redefining backend contracts. Use explicit fixtures, typed handles, valid/invalid connection feedback, inspector editing, execution-state visualization, missing-node preservation, accessibility basics and synthetic graph testing. Produce deterministic evidence, keep the spike isolated from production semantics, do not modify `main`, do not stop for routine approvals, and continue until the spike is COMPLETE FOR CONDUCTOR SYNTHESIS, legitimately BLOCKED with the smallest required intervention documented, or proven INVIABLE. Push the branch, create a review surface/PR if practical, and provide the required handoff with exact SHAs, dependency versions, evidence, limitations and reuse recommendations.

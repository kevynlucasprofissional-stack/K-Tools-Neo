# OC-001 — First Real Capability / Node Pack

Status: READY FOR EXECUTION
Assigned agent: OpenCode
Role: Runtime / Backend Implementation Lead
Working branch: `opencode/first-real-node-pack`
Integration target: `main` by Pull Request only
Issue mirror: GitHub Issue #3 (optional; this file is sufficient even when Issues are unavailable)
Conductor: ChatGPT / Chief Architect / Integration Engineer

> This file is the authoritative task-local instruction for OpenCode. Do **not** depend on GitHub Issues being available. Everything required to start, execute, validate and hand off OC-001 is contained here together with the repository's canonical engineering documents.

---

## 1. Mission

Prove the central architecture of the new K-Tools Neo with **real existing product behavior**:

> one useful K-Tools capability must have exactly one implementation owner and must be callable both directly and as a workflow node without duplicated business logic.

The milestone is not complete merely because a new node exists. The same underlying capability implementation must be exercised by both routes.

Target invariant:

```text
Direct Tool / direct API
          \
           -> Capability implementation <- Workflow Node adapter
          /
Future GUI Tool
```

Do not create this anti-pattern:

```text
legacy/direct implementation A
workflow implementation B
future GUI implementation C
```

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
13. the relevant legacy utilities / K-Tools source files
14. `packages/ktools-core/` source and tests
15. `docs/engineering-journal/CURRENT.md`

Treat code, tests and runtime on the exact ref as current-state evidence. Documentation preserves intent and decisions but does not override contradictory runtime evidence.

---

## 3. Context that must remain true

The Platform Foundation is already promoted. The repository has:

- `packages/ktools-core/` as the UI-independent workflow/runtime authority;
- typed node and port definitions;
- graph validation;
- deterministic DAG execution;
- initial `Artifact` identity/provenance model;
- headless JSON workflow execution;
- Windows + Ubuntu CI;
- existing legacy GUI/utilities that have **not** yet been systematically migrated into reusable capability packs.

The purpose of OC-001 is to cross the boundary from synthetic fixture nodes to the **first real K-Tools capability**.

---

## 4. First task: discovery and candidate ranking

Do not choose a capability only because it is easiest or because its filename is obvious.

Inspect the existing repository and identify realistic candidates. Rank them using evidence from the actual code.

Evaluate each candidate on at least:

| Criterion | Desired property |
|---|---|
| User usefulness | solves a real recurring K-Tools task |
| Determinism | same input/config should produce predictable output |
| Offline/local behavior | preferred for first proof |
| Side-effect risk | low or isolated |
| Testability | can use temporary fixtures |
| Dependency complexity | bounded and reproducible |
| GUI coupling | low or extractable |
| Typed ports | maps cleanly to K-Tools data types |
| Workflow reuse | useful as one step inside larger workflows |
| Failure observability | errors can be classified/tested |
| Cross-platform viability | Windows and Linux CI should be meaningful where applicable |

Likely categories worth inspecting include, but are not automatically selected:

- audio conversion or extraction;
- media transformation;
- file/folder transformation;
- image/PDF transformation;
- deterministic utility operations already present in legacy/root scripts.

Avoid network/auth/browser-heavy capabilities for the **first** production proof unless repository evidence shows that all lower-risk alternatives are architecturally worse.

Record the ranking and selection rationale in the active task/spec documentation or task-local evidence file. If two candidates are materially close and choosing one changes architecture, document the competing hypotheses and choose the one with stronger product + architectural evidence. Do not stop merely to ask for routine approval.

---

## 5. Required architecture

The selected capability must have a single business-logic owner.

A preferred conceptual shape is:

```text
packages/
  ktools-<domain>/
    capability implementation
    public direct API
    tests

packages/ktools-core/
    node adapter / registration contract
```

The exact package boundary may differ if repository evidence justifies another arrangement, but the following are non-negotiable:

1. the workflow node does not duplicate transformation logic;
2. the direct invocation path does not duplicate transformation logic;
3. GUI code is not the implementation owner;
4. workflow semantics remain UI-independent;
5. imported `apps/xcursos-runner` and `apps/yt-dlp-tui` are not modified for this task unless the selected capability genuinely requires them and the Conductor expands scope;
6. temporary test data cannot overwrite or mutate real user files.

---

## 6. Contract requirements

Define explicit inputs, outputs and config.

For a file-producing capability, prefer returning or producing information that can evolve cleanly into `Artifact` provenance rather than passing undocumented filesystem strings everywhere.

At minimum document/test:

- accepted input type(s);
- output type(s);
- required vs optional config;
- invalid configuration behavior;
- source-not-found / unsupported-input behavior where applicable;
- destination semantics;
- overwrite semantics;
- partial-output semantics if failure can occur mid-operation;
- external dependency boundary, if any (for example FFmpeg).

Do not hide environment failures as generic node exceptions if a more precise boundary can be preserved.

---

## 7. Evidence-first implementation loop

Follow the project's quality-first cycle continuously.

### Phase A — Define proof before implementation

Before writing the production implementation, define the evidence that would prove the architecture.

Minimum proof:

1. direct capability invocation on a controlled fixture;
2. workflow-node invocation on a controlled fixture;
3. both routes reach the **same implementation owner**;
4. typed connection/contract is valid;
5. incorrect input/config fails in the expected way;
6. existing Foundation tests remain green.

### Phase B — RED

Create tests or a deterministic failing criterion that demonstrate the missing behavior.

### Phase C — GREEN

Implement the smallest complete production-quality behavior needed to satisfy the defined proof.

### Phase D — REFACTOR

Remove duplicated ownership, clarify boundaries and names, and keep error semantics explicit.

### Phase E — Regression and integration

Run:

- task-local tests;
- `ktools-core` tests;
- CLI smoke where relevant;
- any capability-specific native smoke required by the real runtime boundary;
- root CI through the PR.

Do not weaken existing tests to obtain green.

---

## 8. Required tests

The exact tests depend on the capability, but the resulting suite must demonstrate all of these claims where applicable:

### Capability-level

- happy path;
- invalid input/config;
- deterministic output properties;
- no unintended overwrite;
- dependency-not-found classification if external dependency exists;
- output cleanup/partial-state behavior on failure where meaningful.

### Architecture-level

- direct invocation exercises the selected capability implementation;
- node invocation exercises that same capability implementation;
- no second business-logic implementation exists in the workflow adapter;
- typed input/output definitions correspond to actual runtime behavior.

### Integration-level

- current Foundation test suite remains green;
- root CI reaches actual install/test/smoke boundaries;
- Windows/Ubuntu evidence is recorded for claims that are supposed to be cross-platform.

If the capability requires a dependency that cannot reasonably exist in root CI, define a deterministic unit/contract boundary plus a separately documented native smoke instead of pretending the dependency was exercised.

---

## 9. Ownership boundaries

You own the files necessary for OC-001 implementation and task-local tests/spec evidence.

Do **not** independently change these architectural authorities unless the task makes it unavoidable and you explicitly record why for Conductor review:

- `docs/CONSTITUTION.md`
- `docs/DECISIONS.md`
- `docs/CURRENT_STATE.md`
- `docs/TESTING.md`
- root CI policy
- production desktop/frontend architecture
- `apps/xcursos-runner/` internals
- `apps/yt-dlp-tui/` internals

If a canonical architectural change is required, do not silently edit around it. Record the evidence and proposed decision in the handoff so the Conductor can arbitrate.

---

## 10. Git / branch discipline

Work only on:

`opencode/first-real-node-pack`

Before substantive changes:

- fetch current repository state;
- confirm the branch and exact base;
- compare with current `main`;
- if `main` moved materially, rebase/update safely before continuing or record the divergence.

Do not write directly to `main`.

Do not merge your own PR.

Keep commits reviewable and scoped to OC-001.

---

## 11. Engineering Journal requirements

Create/update task-local engineering evidence for meaningful hypotheses, failures and boundaries.

Journal-worthy examples:

- chosen capability vs rejected candidates;
- GUI/business-logic coupling discovered;
- external dependency/runtime boundary;
- direct and node paths accidentally diverging;
- overwrite/partial-output failure semantics;
- Windows/Linux behavior differences;
- evidence that suggests a core contract needs future change.

Do not record routine noise. Record reusable engineering knowledge.

If canonical Journal editing is reserved by current ownership rules, include proposed Journal entries in the handoff rather than forcing concurrent edits.

---

## 12. Definition of Done

OC-001 reaches `READY FOR INTEGRATION REVIEW` only when all of the following are true:

- [ ] repository candidate discovery was performed;
- [ ] capability choice is justified from evidence;
- [ ] one implementation owner exists;
- [ ] direct invocation is implemented and tested;
- [ ] workflow node invocation is implemented and tested;
- [ ] both routes use the same implementation owner;
- [ ] typed contracts reflect runtime behavior;
- [ ] failure behavior is explicit and tested;
- [ ] test fixtures do not mutate user data;
- [ ] Foundation regressions are green;
- [ ] appropriate native/integration smoke exists for real external boundaries;
- [ ] branch is pushed;
- [ ] PR is opened against `main`;
- [ ] exact-head CI is green or any blocker is classified with evidence;
- [ ] handoff report is complete.

Do not call the task complete merely because code compiles or because a single happy-path test passes.

---

## 13. Required handoff report

At the end, provide a concise but complete handoff containing:

### Identity

- task: `OC-001`;
- branch;
- base SHA;
- head SHA;
- PR number/link if created.

### Capability decision

- candidates evaluated;
- selected capability;
- why it won;
- meaningful rejected alternatives.

### Implementation

- files added/changed;
- implementation owner path;
- direct API path;
- node adapter/registration path;
- input/output/config contract.

### Evidence

- tests run and exact results;
- direct invocation evidence;
- workflow invocation evidence;
- external/native smoke evidence if applicable;
- CI run IDs / status.

### Risks

- remaining limitations;
- cross-platform uncertainty;
- migration debt;
- architectural questions that require Conductor arbitration.

### Journal

- Journal IDs added, or proposed entries if canonical Journal editing was not owned.

### Exact next action

State what the Conductor should inspect or do next. Do not end with a vague "review when possible".

---

## 14. Execution prompt embedded in this file

If you are OpenCode and were only told to read this file, treat the following as your direct instruction:

> Act as the Runtime / Backend Implementation Lead for K-Tools Neo. Execute OC-001 completely on branch `opencode/first-real-node-pack`. Follow `AGENTS.md`, all canonical engineering documents, the playbook rules, and this Work Packet. Inspect the real repository first; rank candidate existing capabilities; choose the strongest first real Node Pack proof; define evidence before implementation; work through RED → GREEN → REFACTOR → regression/integration; preserve one-capability/one-implementation ownership; do not create a second workflow engine; do not alter `main`; do not stop for routine approvals; continue until the task is either READY FOR INTEGRATION REVIEW, legitimately BLOCKED with the smallest required intervention documented, or proven INVIABLE. Open a PR and produce the required handoff with exact SHAs and evidence.

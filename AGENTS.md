# AGENTS.md — K-Tools Neo

All work in this repository follows the project's quality-first engineering protocol.

## Active execution mode

The project owner has activated **ChatGPT Solo Development Mode**.

- ChatGPT currently owns Conductor / Chief Architect / Implementation Engineer / Integration Engineer responsibilities.
- OpenCode, Antigravity and Codex are paused as active writers unless the project owner explicitly re-enables/delegates them.
- Prior audited contributions remain part of repository history and evidence.
- Read `docs/SOLO_DEVELOPMENT_MODE.md` for the current operating contract and reusable prompts.

## Read-before-work order

1. `docs/README.md`
2. `docs/CONSTITUTION.md`
3. `docs/CONSTRAINTS.md`
4. `docs/CURRENT_STATE.md`
5. `docs/ROADMAP.md`
6. `docs/DECISIONS.md`
7. `docs/KNOWN_ISSUES.md`
8. `docs/TESTING.md`
9. `docs/SOLO_DEVELOPMENT_MODE.md`
10. `docs/multi-agent/MAIN_ONLY_POLICY.md`
11. the active spec under `docs/specs/`
12. `docs/engineering-journal/CURRENT.md`
13. relevant code and tests on the exact current `main`
14. multi-agent docs only when parallel delegation is explicitly re-enabled

## Core rules

- Treat code/runtime/tests on the exact current `main` as evidence of current state; docs preserve intent and memory, not magic.
- Revalidate current `main` and relevant hosted CI before material architectural/integration decisions.
- Follow the first unresolved milestone in `docs/ROADMAP.md` whose prerequisites are satisfied, unless repository evidence justifies a documented reorder.
- Do not add new product behavior to the legacy monolith when it can instead become a reusable capability/Node Pack.
- A capability used by a direct Tool/API and by a workflow must have one implementation owner, not duplicated business logic.
- Keep the workflow runtime independent from the visual editor.
- Preserve imported upstream applications under `apps/`; integrate them through adapters unless evidence proves a deeper fork is required.
- Use evidence → RED → GREEN → REFACTOR → regressions → hosted/native validation → memory closure when practical.
- Do not weaken tests/gates to make a candidate green; investigate the first meaningful failing boundary.
- Distinguish mocked/unit evidence from native/integration/cross-platform evidence.
- Update canonical docs and the Engineering Journal when architecture, invariants, failures, evidence boundaries or roadmap state change materially.
- Never commit credentials, cookies, tokens, secrets or sensitive runtime payloads.
- Do not stop for routine approval while an unblocked accepted milestone still has executable work. Stop only at a real terminal state, owner-dependent decision, destructive approval boundary or external limitation.

## Main-only Git policy

The project owner has chosen a simplified **single-main workflow**.

- `main` is the only normal development/integration line unless the project owner explicitly requests otherwise.
- Do not create task branches, draft branches, integration branches or PR-only staging as the default workflow.
- Temporary branches are allowed only for destructive recovery/isolation or when explicitly requested.
- Never force-push over human work.
- If concurrent writes are plausible, re-read/fetch current head before each material write.
- Keep commits coherent and leave `main` understandable at each accepted checkpoint.
- GitHub Actions is a required hosted evidence boundary for subsystems currently covered by CI.

## Product architecture invariants

- `ktools-core` is the workflow/runtime authority.
- Node Packs are the extension boundary for reusable capability families.
- Direct use and workflow use share capability owners.
- `@xyflow/react` is the leading editor interaction layer, not the workflow engine.
- Future UI execution state comes from runtime/Run Journal contracts, not a frontend state machine pretending to be the engine.
- Unknown/missing Node Packs must be preservable in workflow serialization rather than silently deleting data.
- Artifact provenance, durable execution and recovery precede broad expensive-media automation.

## Historical multi-agent material

`docs/multi-agent/` remains useful history, research and handoff evidence. Its role/branch instructions do not override the current Solo Mode or main-only policy unless the project owner explicitly reactivates parallel agents.
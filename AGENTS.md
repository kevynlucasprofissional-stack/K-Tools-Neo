# AGENTS.md — K-Tools Neo

All agents working in this repository must follow the project's quality-first engineering protocol.

## Read-before-work order

1. `docs/README.md`
2. `docs/CONSTITUTION.md`
3. `docs/CONSTRAINTS.md`
4. `docs/CURRENT_STATE.md`
5. `docs/DECISIONS.md`
6. `docs/KNOWN_ISSUES.md`
7. `docs/TESTING.md`
8. `docs/multi-agent/MAIN_ONLY_POLICY.md`
9. the active spec under `docs/specs/`
10. `docs/engineering-journal/CURRENT.md`
11. `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` when work is delegated or parallel
12. relevant code and tests on the exact current `main`

## Core rules

- Treat code/runtime/tests on the exact current `main` as evidence of current state; docs preserve intent and memory, not magic.
- Do not add new product behavior to the legacy monolith when it can instead become a reusable node capability.
- A capability used by a traditional tool screen and by a workflow must have one implementation owner, not duplicated business logic.
- Keep the workflow runtime independent from the visual editor.
- Preserve imported upstream applications under `apps/`; integrate them through adapters unless evidence proves a deeper fork is required.
- Before a material write, fetch/pull `main`, record the exact SHA and ensure the task still fits current state.
- Use RED → GREEN → REFACTOR when practical and define evidence before implementation.
- Update canonical docs and the Engineering Journal when architecture, invariants, failures or evidence boundaries change.
- Never commit credentials, cookies, tokens, secrets or sensitive runtime payloads.

## Main-only collaboration policy

The project owner has chosen a simplified **single-main workflow**.

- `main` is the only active development/integration line unless the project owner explicitly requests otherwise.
- Do not create task branches, draft branches, integration branches or PR-only staging as the default workflow.
- OpenCode and Antigravity may commit/push their assigned, non-overlapping work directly to `main`.
- Separate local clones/worktrees are still allowed for process isolation, but they should track `main`, not create separate long-lived histories.
- Before every push: `git fetch origin`, `git pull --rebase origin main`, rerun the relevant tests, then push only if the owned paths remain conflict-free.
- If another agent changed the same file/contract, do not guess through the conflict. Stop that overlapping edit, re-read current `main`, and coordinate ownership through the Conductor.
- Existing Work Packets or historical docs that say "work on branch X", "open a PR", or "do not write to main" are overridden by `docs/multi-agent/MAIN_ONLY_POLICY.md` and this section.
- Temporary branches are allowed only when the project owner explicitly asks for one or when a destructive recovery operation requires isolation.

## Multi-agent roles

- ChatGPT is the Conductor / Chief Architect / Integration Engineer unless the project owner explicitly changes that role.
- OpenCode is the default Runtime / Backend Implementation Lead.
- Antigravity is the default Frontend / UX / Product Prototype Lead.
- Codex is intentionally excluded from the K-Tools development pool until the project owner changes that constraint.
- Parallel work requires disjoint path/contract ownership. Parallel agents must not edit the same contract at the same time.
- Every handoff must include starting SHA, resulting `main` SHA, task IDs, changed files, tests/evidence, Journal/known-issue impact, risks and exact next action.
- See `docs/multi-agent/MAIN_ONLY_POLICY.md` and `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` for the operating model.

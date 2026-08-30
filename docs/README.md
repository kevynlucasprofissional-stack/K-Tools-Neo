# K-Tools Neo Engineering Context

This directory is the canonical engineering memory for the platform transition.

## Required read order

1. `CONSTITUTION.md`
2. `CONSTRAINTS.md`
3. `CURRENT_STATE.md`
4. `DECISIONS.md`
5. `KNOWN_ISSUES.md`
6. `TESTING.md`
7. active `specs/<change>/spec.md`
8. its `plan.md`, `tasks.md` and `evidence.md`
9. `engineering-journal/CURRENT.md`
10. `multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` when work is delegated or parallel
11. relevant research under `research/` when referenced by the active spec/decision

## Durable reference studies

- `research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md` — source-based study of n8n, Activepieces, LiteGraph.js, Rete.js, ComfyUI, Node-RED and xyflow, including reuse/licensing boundaries and K-Tools architecture implications.

## Multi-agent coordination

- `multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` — authority model, branch/worktree strategy, ownership map, integration/handoff protocol and staged delegation plan for ChatGPT, OpenCode and Antigravity.

The repository ref and runtime remain the source of truth for what exists now. These documents preserve target state, constraints, decisions, evidence boundaries and lessons.

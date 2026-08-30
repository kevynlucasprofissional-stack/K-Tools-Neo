# K-Tools Neo — Agent Work Packets

These files are the **local, versioned execution instructions** for implementation agents. They exist so an agent does not need GitHub Issues, GitHub API access, MCP GitHub or the `gh` CLI to understand its assignment.

## Active Git policy

The project now uses a **main-only workflow**.

Read `docs/multi-agent/MAIN_ONLY_POLICY.md` before executing any packet.

Any older text inside a Work Packet that says to use a dedicated branch, avoid writing to `main`, open a PR, or wait for merge is overridden by the current main-only policy unless the project owner explicitly says otherwise for that task.

## Current packets

### OpenCode

Read and execute:

`docs/multi-agent/work-packets/OC-001-FIRST-REAL-NODE-PACK.md`

Active Git target: `main`.

Purpose: select and implement the first real reusable K-Tools capability/Node Pack, proving that direct usage and workflow-node usage share one implementation owner.

### Antigravity

Read and execute:

`docs/multi-agent/work-packets/AG-001-XYFLOW-EDITOR-SPIKE.md`

Active Git target: `main`.

Purpose: continue validating the React + TypeScript + `@xyflow/react` editor interaction model under `spikes/xyflow-editor/` without creating a second workflow engine.

## How to delegate

For OpenCode:

```text
Work from the latest main. Read AGENTS.md, docs/multi-agent/MAIN_ONLY_POLICY.md and docs/multi-agent/work-packets/OC-001-FIRST-REAL-NODE-PACK.md, then execute OC-001 completely. Stay inside your backend/runtime ownership, pull --rebase origin main before pushing, run the required tests, and push the validated result directly to main. Do not create a task branch unless I explicitly ask.
```

For Antigravity:

```text
Work from the latest main. Read AGENTS.md, docs/multi-agent/MAIN_ONLY_POLICY.md and docs/multi-agent/work-packets/AG-001-XYFLOW-EDITOR-SPIKE.md, then continue AG-001 completely. Stay inside the frontend/spike ownership, pull --rebase origin main before pushing, run the required tests, and push the validated result directly to main. Do not create a task branch unless I explicitly ask.
```

## Authority

Repository-wide authority remains with `AGENTS.md`, `docs/multi-agent/MAIN_ONLY_POLICY.md` and the canonical engineering documents under `docs/`. Work Packets define task-local goals and evidence, but historical branch/PR instructions inside them no longer control Git workflow.

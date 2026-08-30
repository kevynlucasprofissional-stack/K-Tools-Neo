# K-Tools Neo — Agent Work Packets

These files are the **local, versioned execution instructions** for implementation agents. They exist specifically so an agent does not need GitHub Issues, GitHub API access, MCP GitHub, or the `gh` CLI to understand its assignment.

## Current packets

### OpenCode

Read and execute:

`docs/multi-agent/work-packets/OC-001-FIRST-REAL-NODE-PACK.md`

Working branch:

`opencode/first-real-node-pack`

Purpose: select and implement the first real reusable K-Tools capability/Node Pack, proving that direct usage and workflow-node usage share one implementation owner.

### Antigravity

Read and execute:

`docs/multi-agent/work-packets/AG-001-XYFLOW-EDITOR-SPIKE.md`

Working branch:

`agent-antigravity/xyflow-editor-spike`

Purpose: validate the future React + TypeScript + `@xyflow/react` editor interaction model in an isolated spike without creating a second workflow engine.

## How to delegate

After the agent has the repository locally and has fetched the latest refs, the human instruction can be very small.

For OpenCode:

```text
Read AGENTS.md and execute docs/multi-agent/work-packets/OC-001-FIRST-REAL-NODE-PACK.md completely. Work only on the branch assigned in that Work Packet. Follow the playbook until a terminal state and do not merge to main.
```

For Antigravity:

```text
Read AGENTS.md and execute docs/multi-agent/work-packets/AG-001-XYFLOW-EDITOR-SPIKE.md completely. Work only on the branch assigned in that Work Packet. Follow the playbook until a terminal state and do not merge to main.
```

## Authority

The Work Packet is task-local instruction. Repository-wide authority remains with `AGENTS.md` and the canonical engineering documents under `docs/`. If a Work Packet and a newer canonical architectural decision conflict, the agent must record the conflict and hand it to the Conductor rather than silently choosing a new architecture.

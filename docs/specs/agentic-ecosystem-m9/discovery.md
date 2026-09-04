# Discovery: M9 — Agentic Workstation Integration + Capability Ecosystem

## Background
Milestones M6, M7, and M8 established:
- Typed capability manifests and MCP servers (M6);
- Scoped safety, policy classification, and system capabilities (M7);
- Cross-platform host provider architecture for Windows and Linux/Omarchy (M8).

Milestone M9 delivers the bridge between K-Tools Neo as a deterministic host execution substrate and high-level agent orchestrators (specifically Hermes Workstation, as well as multi-agent frameworks).

## Strategic Invariants
1. **Separation of Concerns**:
   - Hermes Workstation owns conversational intent, memory, task planning, and user approvals.
   - K-Tools Neo owns deterministic local capability execution, DAG workflows, artifacts, and execution receipts.
   - K-Tools does NOT create a competing LLM planner or second task database.
2. **Policy Handshake**:
   - Operations classified as requiring confirmation halt before execution unless the caller provides explicit authorization tokens.
3. **Workflow-as-Capability**:
   - A multi-step workflow defined in JSON can be projected as a single named, typed capability, allowing an agent to execute an entire pipeline with a single tool call without having to re-synthesize low-level nodes.
4. **Ecosystem Readiness**:
   - Deterministic readiness verification for runtime tools, dependencies, and host capabilities.

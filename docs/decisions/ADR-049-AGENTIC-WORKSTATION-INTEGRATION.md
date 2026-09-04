# ADR 049: Agentic Workstation Integration + Capability Ecosystem

## Date
2026-09-03

## Status
Accepted

## Context
With Milestones M6 (Agent Capability Interface V1), M7 (System Capabilities, Events + Scoped Safety), and M8 (Cross-Platform Host Provider Architecture) established, K-Tools Neo possessed a rich suite of local capabilities. Milestone M9 addresses the integration of K-Tools into the broader AI agent ecosystem (specifically targeting Hermes Workstation and autonomous agent harnesses) without sacrificing its independent value for human users and visual workflows.

## Decision
1. **Hermes Capability Adapter (`ktools_core.adapters.hermes`)**:
   - Implemented `HermesCapabilityAdapter` translating Hermes action requests into canonical K-Tools capability invocations.
   - Enforces `CapabilityScope` constraints upfront.
   - Implements the policy confirmation handshake: operations marked `destructive_mutation` (or requiring elevation) halt with status `REQUIRES_CONFIRMATION` unless the request presents `human_confirmed: true`.
   - Projects standard `ExecutionReceipt` into Hermes-compatible action results containing outputs, artifact metadata (URIs, hashes), duration, and receipt token.

2. **Workflow-as-Capability (`ktools_core.adapters.workflow_capability`)**:
   - Implemented `register_workflow_as_capability` allowing any valid Workflow DAG to be wrapped and registered as a single typed node in `NodeRegistry`.
   - Supports automated input port injection and feeder synthesis via `core.literal` for unlinked entry ports.
   - Executes multi-step workflows deterministically through `WorkflowEngine`, capturing node run journals and routing terminal outputs.

3. **Ecosystem Readiness Inspection (`ktools_core.readiness`)**:
   - Implemented `check_readiness(registry)` producing typed `ReadinessReport` inspecting Python runtime, host provider capabilities, node packs, and external binary dependencies (FFmpeg/FFprobe).

4. **Invariants Preserved**:
   - K-Tools remains a deterministic host execution substrate; Hermes Workstation remains the owner of user intent, tasks, and conversation.
   - Zero duplicate implementations: Tools, Workflows, and Agents invoke the exact same capability handlers.

## Consequences
- Agents can safely call atomic capabilities or entire validated multi-node workflow pipelines with structured receipts and pre-flight safety policies.
- K-Tools integrates cleanly with Hermes Workstation, Claude Code, OpenCode, Codex, and Antigravity.

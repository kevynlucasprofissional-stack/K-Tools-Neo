# ADR 046: Agent Capability Interface V1

## Date
2026-09-03

## Status
Accepted

## Context
Milestones M0-M5 produced 34 robust Node Packs. However, AI agents and external orchestrators (such as Hermes Workstation, Claude Code, Codex, Antigravity) needed a stable, machine-consumable interface to discover and invoke host capabilities without having to synthesize ad-hoc multi-node DAG workflows or parse unstructured console logs.

## Decision
1. **Capability Manifest (`ktools_core.manifest`)**:
   - `CapabilityManifest` is an automated, versioned machine-readable projection derived directly from `NodeRegistry`.
   - Classifies each capability by `SideEffectClass` (`PURE`, `READ_ONLY`, `IDEMPOTENT_MUTATION`, `DESTRUCTIVE_MUTATION`, `UNCONSTRAINED`), inputs/outputs, and safety requirements.
   - It is a pure projection, preserving the single-implementation-owner invariant.

2. **Execution Receipt (`ktools_core.receipt`)**:
   - Standardizes output into an `ExecutionReceipt` carrying status, timestamps, duration, safe inputs, outputs, Artifact records (with URIs and SHA-256 digests), warnings, and diagnostic session IDs.

3. **Unified Capability Invoker (`ktools_core.invoker`)**:
   - Single-capability direct execution boundary that validates port types, executes the canonical handler, records RunJournal events, and returns `ExecutionReceipt`.

4. **Multi-Transport Support**:
   - CLI: `ktools capabilities list`, `describe`, and `invoke`.
   - MCP Server: Standard JSON-RPC Model Context Protocol endpoint over stdio (`ktools mcp`).
   - Skill Playbook: `skills/ktools-capabilities/SKILL.md` for agent consumers.

## Consequences
- Agents can safely query, inspect, and invoke any K-Tools capability with machine-consumable receipts.
- Zero duplicate business logic: the same handlers are executed by CLI, MCP, Direct API, and WorkflowEngine.

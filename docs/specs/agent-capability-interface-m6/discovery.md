# Discovery: M6 — Agent Capability Interface V1

## Problem Context
Milestones M0 through M5 established a robust platform of 34 Node Packs, a deterministic DAG engine, SQLite RunJournal durable execution, diagnostics with secret redaction, and semantic caching.
However, AI agents (such as Hermes, Claude Code, Codex, Antigravity) currently have no standardized, machine-consumable surface to:
1. Discover the exact list of capabilities, inputs/outputs, schemas, and safety metadata (`CapabilityManifest`).
2. Directly invoke a single capability without assembling a synthetic multi-node DAG, while retaining full Artifact occurrence, RunJournal durability, and Diagnostics guarantees.
3. Receive a concise, structured `ExecutionReceipt` containing timestamps, status, outputs, artifacts, warnings, and diagnostic references.
4. Interact over standard machine protocols (CLI JSON and Model Context Protocol - MCP).

## Architectural Invariants to Uphold
1. **One Implementation Owner**: The capability logic must remain exclusively inside its Node Pack. The manifest, CLI, and MCP adapters must project from this owner, never creating duplicate business logic.
2. **Contract Parity**: Workflow execution and agent invocation must validate the identical typed port contracts (`DataType`).
3. **No Agent Lock-in**: K-Tools Neo is host- and agent-agnostic. Hermes is a reference consumer, but the interface must conform to open standards (CLI + MCP + Skills).
4. **Safety & Receipts**: Every invocation returns an explicit, machine-readable `ExecutionReceipt` rather than prose logs.

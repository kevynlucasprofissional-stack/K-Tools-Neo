# Discovery: M7 — System Capabilities, Events + Scoped Safety

## Problem Context
While M0-M5 focused on file, document, and media transformation and M6 established the Agent Capability Interface, an agentic operating environment needs bounded, deterministic system capabilities (process lifecycle, clipboard exchange, machine health, OS notifications) alongside strict security scopes and event streams.

Agents must not be granted unconstrained host authority. Invocations must operate under explicit, caller-defined `CapabilityScope` restrictions (e.g. allowed path roots, no-network, no-subprocess, non-destructive).
Additionally, changes in host state (e.g. process termination, job completion) must be streamable back to agents as structured events without K-Tools becoming a conversational planner.

## Architectural Invariants
1. **One Implementation Owner**: Host operations live in `packages/ktools-system`, projecting both as workflow nodes and direct capabilities.
2. **Least Privilege Enforcement**: If a caller executes a capability outside its declared `CapabilityScope` (e.g. writing outside `allowed_roots`), execution fails closed with a `ScopeViolationError` inside the `ExecutionReceipt`.
3. **Policy Handshake**: K-Tools exposes action classification metadata (`allow`, `sandbox`, `require_human_confirmation`, `deny`) for upstream orchestrators (e.g. Hermes Workstation) to enforce user approvals.
4. **Structured Event Stream**: `SystemEventStream` produces JSON-safe typed records, attaching correlation and execution receipts.

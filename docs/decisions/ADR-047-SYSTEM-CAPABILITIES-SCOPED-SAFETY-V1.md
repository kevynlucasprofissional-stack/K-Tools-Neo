# ADR 047: System Capabilities, Events + Scoped Safety V1

## Date
2026-09-03

## Status
Accepted

## Context
Following Milestone M6 (Agent Capability Interface V1), K-Tools was established as an execution substrate for AI agents and automated workflows. However, agents operating on host machines require safe, structured access to system-level operations (subprocess execution, host health diagnostics, clipboard access, notifications) without compromising security through blanket elevation or unconstrained filesystem access.

## Decision
1. **Scoped Safety Model (`packages/ktools-system/src/ktools_system/models.py`)**:
   - Implemented `CapabilityScope` providing fine-grained, caller-specified constraints: `allowed_roots`, `allow_subprocess`, `allow_network`, `allow_destructive`, and `require_elevation`.
   - Path operations validate against `allowed_roots`, raising `ScopeViolationError` upon path traversal or escape attempts.
   - Provided `classify_action(side_effect_class)` producing actionable `PolicyAction` hints (`allow`, `constrain`, `require_human_confirmation`, `deny`) for external orchestrators (such as Hermes Workstation).

2. **System Node Pack (`packages/ktools-system/src/ktools_system/node.py`)**:
   - `system.process_launch`: Bounded subprocess execution with timeout, output capture (stdout/stderr), and exit code reporting.
   - `system.clipboard_read` / `system.clipboard_write`: Text clipboard operations with cross-platform fallback.
   - `system.host_health`: Non-invasive host metric inspection (platform, CPU count, Python runtime, disk capacity and percentage used).
   - `system.notify`: User-attention notification publishing.

3. **Structured Event Stream (`packages/ktools-system/src/ktools_system/events.py`)**:
   - Implemented `SystemEventStream` and `SystemEvent` schema offering pub/sub event subscriptions, history retention, and thread-safe event emission for process completion, failures, and alerts.

4. **Integration & Conformance**:
   - Registered `ktools_system.node` within `ktools_core.registry.load_all_installed_node_packs`.
   - Verified that all system capabilities project into `CapabilityManifest`, MCP Server, Direct API, and CLI.

## Consequences
- Agents can safely invoke host capabilities under explicit boundary scopes.
- K-Tools remains a deterministic executor rather than a conversational planning engine, providing structured receipts and event feeds to upstream controllers.

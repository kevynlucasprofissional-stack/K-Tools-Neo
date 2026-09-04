# Specification: M7 — System Capabilities, Events + Scoped Safety

## Objective
Establish `packages/ktools-system` delivering:
1. `CapabilityScope`: Least-privilege policy model enforcing `allowed_roots`, `allow_subprocess`, `allow_network`, `allow_destructive`.
2. Core System Nodes:
   - `system.process_launch`: Safe subprocess execution with bounded timeout, stdout/stderr capture, and exit code.
   - `system.clipboard_read` / `system.clipboard_write`: Text clipboard interchange.
   - `system.host_health`: CPU, memory, disk free, platform information.
   - `system.notify`: User notification / toast request.
3. `SystemEventStream`: Subscription-based structured event emission (`PROCESS_EXITED`, `HEALTH_ALERT`, `NOTIFICATION_SENT`).
4. Policy handshake classification metadata.

## Safety Contracts
- If `allow_subprocess=False`, invoking `system.process_launch` raises `ScopeViolationError`.
- If a path input is outside `allowed_roots`, the capability fails immediately before accessing the filesystem.
- Sensitive values (tokens, credentials) in process arguments are redacted through M3 Diagnostics.

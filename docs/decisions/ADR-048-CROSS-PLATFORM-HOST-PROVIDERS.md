# ADR 048: Cross-Platform Host Provider Architecture

## Date
2026-09-03

## Status
Accepted

## Context
K-Tools Neo operations have historically targeted Windows desktop execution. With the introduction of system capabilities in M7 and agentic integration targets (including Linux reference environments such as Omarchy), the runtime required a provider architecture that maintains a single typed capability catalog while encapsulating platform-specific mechanisms.

## Decision
1. **Generic Host Provider Contract (`ktools_core.host.provider`)**:
   - Established `HostPlatform` (`WINDOWS`, `LINUX`, `DARWIN`, `UNKNOWN`) and `HostCapability` (`PROCESS_LAUNCH`, `CLIPBOARD_SYNC`, `HOST_HEALTH`, `NOTIFICATIONS`, `ELEVATION`, `FS_WATCH`).
   - Defined `HostProvider` abstract interface and explicit capability negotiation (`is_capability_supported`, `supported_capabilities`).
   - Created `HostCapabilityUnsupportedError` to enforce fail-closed behavior when an unsupported capability is requested.

2. **Windows Desktop Baseline (`ktools_core.host.windows`)**:
   - Implemented `WindowsHostProvider` with Win32 ctypes clipboard API, process execution, disk/platform metrics, and Windows notification delivery.

3. **Linux / Omarchy Reference Provider (`ktools_core.host.linux`)**:
   - Implemented `LinuxHostProvider` supporting standard Posix process execution, `/proc` and `statvfs` health metrics, Freedesktop `notify-send`, and `wl-copy`/`xclip` clipboard integration.

4. **Dynamic Detection and Injection**:
   - Implemented `get_active_host_provider()` with platform auto-detection and `set_active_host_provider(...)` for testing and cross-platform simulation.

5. **Delegation in `ktools-system`**:
   - Refactored `ktools_system.clipboard`, `ktools_system.health`, `ktools_system.process`, and `ktools_system.node` to delegate to `get_active_host_provider()`.

6. **Cross-Host Conformance Suite**:
   - Validated semantic equivalence, error semantics, and output shapes via `packages/ktools-core/tests/test_host_provider_conformance.py`.

## Consequences
- K-Tools capabilities operate transparently on both Windows and Linux hosts without duplicating business logic or branching inside workflow nodes.
- Unsupported platform capabilities fail explicitly with clear diagnostics rather than silent degradation.

# Specification: M8 — Cross-Platform Host Provider Architecture

## Objective
Establish `ktools_core.host` defining:
1. `HostPlatform` enum (`WINDOWS`, `LINUX`, `DARWIN`, `UNKNOWN`).
2. `HostCapability` enum (`PROCESS_LAUNCH`, `CLIPBOARD_SYNC`, `HOST_HEALTH`, `NOTIFICATIONS`, `ELEVATION`).
3. `HostCapabilityUnsupportedError` exception.
4. `HostProvider` abstract interface.
5. Concrete implementations:
   - `WindowsHostProvider`: Full support for process launch, clipboard, host health, and notifications.
   - `LinuxHostProvider`: Omarchy / Linux reference provider with process launch, clipboard sync, host health, and notifications.
6. Detection & Provider Injection:
   - `get_active_host_provider() -> HostProvider`
   - `set_active_host_provider(provider: HostProvider | None) -> None`
7. Conformance Test Suite:
   - `test_host_provider_conformance.py` verifying semantic parity across all providers.

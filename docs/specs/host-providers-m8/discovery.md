# Discovery: M8 — Cross-Platform Host Provider Architecture

## Background
K-Tools Neo originated on Windows with desktop automations and legacy scripts. Milestones M6 and M7 established typed capability manifests, execution receipts, and system capabilities (`system.process_launch`, `system.host_health`, `system.clipboard_read`, `system.clipboard_write`, `system.notify`).

To enable execution across diverse desktop and workstation hosts (including Linux and Omarchy environments) without fragmenting the single-owner capability architecture, K-Tools requires a clean **Host Provider** abstraction.

## Core Architectural Requirements
1. **Explicit Capability Negotiation**:
   - A host provider declares exactly which capabilities it supports natively.
   - Unsupported capabilities must fail closed with an explicit, typed error (`HostCapabilityUnsupportedError`) rather than pseudo-emulation or silent corruption.
2. **Windows Canonical Baseline**:
   - Win32 native APIs (`ctypes.windll`, PowerShell toasts, NTFS path handling).
3. **Linux / Omarchy Reference Provider**:
   - `LinuxHostProvider` leveraging Linux standard conventions (`/proc`, `statvfs`, `notify-send`, Freedesktop standards) and Omarchy CLI contracts where present.
4. **Conformance Testing**:
   - Provider test suite ensuring identical receipt shape, error handling, and scope adherence regardless of host OS.

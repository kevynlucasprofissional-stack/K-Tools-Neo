# Specification: M6 — Agent Capability Interface V1

## Objective
Establish the canonical Agent Capability Interface V1 in `packages/ktools-core`, providing:
1. `CapabilityManifest`: Automatic machine-readable capability projection from `NodeRegistry`.
2. `ExecutionReceipt`: Structured machine receipt detailing status, inputs, outputs, artifacts, duration, and diagnostic IDs.
3. `CapabilityInvoker`: Unified single-capability execution boundary sharing `WorkflowEngine` invariants (validations, journal, diagnostics, cache).
4. `CLI Capability Commands`: `ktools capabilities list`, `describe`, and `invoke`.
5. `MCP Server`: Standard JSON-RPC Model Context Protocol endpoint exposing capabilities as tools.
6. `Skill Specification`: Agent playbook for Hermes and external harnesses.

## Data Models

### 1. `SideEffectClass` (Enum)
- `PURE`: No host side effects (e.g. calculation, schema validation).
- `READ_ONLY`: Reads host filesystem or state without mutations (e.g. `folder.scan_files`, `filesystem.structure_report`).
- `IDEMPOTENT_MUTATION`: Produces outputs or updates files where repeating produces identical state (e.g. `media.convert_audio`, `pdf.merge`).
- `DESTRUCTIVE_MUTATION`: Overwrites or deletes existing host resources.
- `UNCONSTRAINED`: Arbitrary subprocess or external execution.

### 2. `CapabilityDefinition` (Dataclass)
- `capability_id`: str (e.g. `media.convert_lossless_alac`)
- `version`: str (e.g. `1.0.0`)
- `title`: str
- `description`: str
- `category`: str
- `inputs`: dict of input specifications (type, required, default, description)
- `outputs`: dict of output specifications (type, description)
- `side_effect_class`: SideEffectClass
- `cache_policy`: CachePolicy
- `network_required`: bool
- `privilege_elevation`: bool
- `supports_dry_run`: bool

### 3. `ExecutionReceipt` (Dataclass)
- `receipt_id`: str
- `capability_id`: str
- `version`: str
- `status`: `SUCCESS` | `FAILED` | `CACHED` | `INTERRUPTED` | `PARTIAL_SUCCESS`
- `started_at`: str (ISO 8601)
- `completed_at`: str (ISO 8601)
- `duration_seconds`: float
- `inputs`: dict (safely normalized)
- `outputs`: dict (safely normalized)
- `artifacts`: list of Artifact records (id, uri, sha256, mime_type, size_bytes)
- `warnings`: list of str
- `cache_hit`: bool
- `error`: optional error dict (type, message, details)
- `diagnostics_session_id`: optional str

## Verification Plan
1. Unit tests for `CapabilityManifest` projection from `NodeRegistry`.
2. Unit tests for `CapabilityInvoker` and `ExecutionReceipt` generation.
3. CLI execution tests for `ktools capabilities list` and `invoke`.
4. MCP Server protocol tests for `tools/list` and `tools/call`.
5. End-to-end parity test proving identical results between WorkflowEngine and CapabilityInvoker.

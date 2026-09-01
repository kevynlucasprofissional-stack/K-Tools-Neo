# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.

Canonical sequencing guide: `docs/ROADMAP.md`.

OpenCode, Antigravity and Codex remain paused as active writers unless the project owner explicitly re-enables them.

## M0 — Platform Foundation — RESOLVED

Working runtime base:

- UI-independent `packages/ktools-core/`;
- typed node/port contracts and DAG validation/execution;
- initial Artifact model;
- headless workflow CLI;
- Windows/Linux hosted CI;
- bounded imported `xcursos-runner` and `yt-dlp-tui` subsystems.

## M1 — First official Node Pack — RESOLVED

`packages/ktools-json/` proves one capability owner shared by direct API and `json.split` workflow use, with classified failures, deterministic output, collision safety and hosted evidence.

Audit: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` remains evidence that React + `@xyflow/react` is a credible editor interaction layer while `ktools-core` remains runtime truth.

## M2 — Durable Execution V1 — RESOLVED

K-Tools has an optional injected Run Journal and stdlib SQLite persistence for ordered run/node lifecycle history.

Delivered:

- `RUN_STARTED`, node start/success/failure, run success/failure;
- explicit interrupted reconciliation;
- durable run/node projections;
- error/output metadata;
- JSON-safe conservative serialization;
- run history/detail/event query API;
- `--journal <sqlite-db>` on core and JSON CLIs;
- real `json.literal -> json.split` success/failure evidence.

Hosted evidence includes run `33552906228` and post-hardening run `33553179743`, both green across Windows/Linux Python lanes plus the xyflow job.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

## Roadmap reorder — diagnostics now precede recovery/cache

The project owner explicitly requested a complete diagnostic/logging system able to reconstruct unexpected executions, including terminal/subprocess output, failures, inconsistent results, low-quality model observations, decisions, batches and end-of-run reports.

Because future cache/recovery, FFmpeg, browser and downloader work would otherwise need diagnostics retrofitted later, the roadmap now makes **Diagnostics + Support Bundle the M3 prerequisite**.

Artifact lifecycle/recovery/cache moved to M4.

## M3 — Diagnostics, Structured Logging + Support Bundle — ACTIVE

Spec: `docs/specs/diagnostics-support-bundle-v1/spec.md`.

Implementation currently on `main` includes:

### Structured diagnostic events

`packages/ktools-core/src/ktools_core/diagnostics.py` provides:

- `DiagnosticSeverity`: DEBUG / INFO / WARNING / ERROR / CRITICAL;
- event kinds for logs, decisions, metrics, batches, anomalies, exceptions, subprocesses and lifecycle;
- workflow/run/node/stage/batch correlation fields;
- safe structured context;
- traceback capture;
- helpers for explicit decisions, metrics, batches and anomalies.

### Safe sharing / redaction

Diagnostic serialization now:

- reuses the conservative core JSON-safe boundary;
- redacts recognized token/API-key/password/secret/cookie/authorization patterns;
- redacts secret-like command arguments;
- avoids arbitrary unknown-object `repr()` capture;
- bounds structured strings;
- does not snapshot environment variables wholesale.

Security regression tests seed fake secrets and require them to be absent from reports/event streams/raw captured output.

### Subprocess / PowerShell boundary

`DiagnosticsSession.run_subprocess(...)` records:

- redacted command identity;
- cwd where supplied;
- start/completion;
- duration;
- return code;
- stdout/stderr files;
- non-zero exit;
- timeout;
- launch failure.

A platform-conditional test exercises PowerShell (`pwsh`/`powershell`) when present.

This boundary is intended to become the common future entry point for FFmpeg/FFprobe and other subprocess-heavy capabilities.

### Standard Python logging

`DiagnosticLogHandler` bridges stdlib `logging` messages and logged exceptions into the same Diagnostics Session without serializing the arbitrary full LogRecord dictionary.

### Automatic support bundle

A finalized Diagnostics Session creates:

```text
<diagnostics-root>/<session-id>/
  diagnostics.jsonl
  report.json
  report.md
  raw/
  support-bundle.zip
```

Both current first-party workflow CLIs now enable diagnostics by default and expose:

```text
--diagnostics-dir <dir>
--no-diagnostics
```

Successful `--json` output contains `diagnosticBundle`; handled validation/execution/unexpected errors print the generated bundle path before returning their error code.

### Engine correlation

`WorkflowEngine` accepts an optional `DiagnosticsSession` independently of Run Journal. When supplied, node/run start/success/failure observations are correlated with real run/workflow/node IDs.

Run Journal remains lifecycle authority; diagnostics supplements it rather than replacing it.

### Abnormal termination recovery

`recover_abandoned_sessions(...)` can package a stale diagnostics directory that contains an event stream but no final report, preserving the last durable evidence after a crash/forced termination/machine shutdown.

Important safety boundary: absence of `report.json` alone does not prove process death. Recovery therefore requires a minimum staleness age by default; age `0` is only for callers with independent evidence that no live process owns the session. A future process ownership/lease model may strengthen this further.

## M3 still open

Do **not** mark M3 resolved yet.

Remaining closure work includes:

- make human-readable `report.md` as complete as `report.json` for batches, metrics, subprocesses, result summaries and journal history;
- finish interruption/Ctrl+C CLI semantics;
- ensure real JSON Node Pack success/failure support-bundle tests pass on Windows/Linux;
- inspect latest hosted CI and fix any regressions;
- record exact-head evidence and test counts;
- update Decisions / Testing / Engineering Journal / spec evidence;
- close M3 only after the final documentation head is green.

## Later roadmap

M4 becomes Artifact Lifecycle + Recovery + Semantic Cache, now explicitly required to explain cache reuse/invalidation through M3 diagnostics.

Subsequent milestones cover official local Node Packs, imported app adapters, UI contract API, production workflow editor, ready-made Tools, desktop packaging, agent-first composition and release hardening.

## Next exact action

Finish Diagnostics + Support Bundle V1 rather than starting artifact cache work. The immediate implementation target is complete human-report rendering plus interruption behavior, followed by exact-head hosted Windows/Linux acceptance.

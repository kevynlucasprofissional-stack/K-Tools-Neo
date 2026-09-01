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

- run/node lifecycle events and query projections;
- explicit interruption reconciliation;
- error/output metadata;
- conservative JSON-safe serialization;
- run history/detail/event query API;
- `--journal <sqlite-db>` on core and JSON CLIs;
- real `json.literal -> json.split` success/failure evidence.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

## M3 — Diagnostics, Structured Logging + Support Bundle — RESOLVED / PROMOTED

The project now has a first-class diagnostic/support layer before cache/recovery, media, browser and imported-app integration work.

Spec/evidence/final report: `docs/specs/diagnostics-support-bundle-v1/`.

### Structured diagnostics

`ktools-core` now provides:

- DEBUG / INFO / WARNING / ERROR / CRITICAL severities;
- LOG / DECISION / METRIC / BATCH / ANOMALY / EXCEPTION / SUBPROCESS / LIFECYCLE event kinds;
- run/workflow/node/stage/batch correlation;
- explicit decision reasons, metrics, batch observations and anomalies;
- exception type/message/traceback capture;
- `DiagnosticLogHandler` bridge for stdlib Python logging.

### Safe sharing

Support material uses a conservative safe-sharing boundary:

- common token/API-key/password/secret/cookie/Authorization patterns are redacted recursively;
- secret-like command arguments and URL query values are redacted;
- arbitrary unknown-object `repr()`/reflection is avoided;
- structured strings are bounded;
- environment variables are not snapshotted wholesale;
- captured subprocess stdout/stderr is redacted before becoming shareable.

Seeded-secret regression tests exercise these boundaries.

### Subprocess / PowerShell diagnostics

`DiagnosticsSession.run_subprocess(...)` records command identity, cwd, start/end, duration, return code, stdout/stderr files, non-zero exit, timeout and launch failure.

Hosted acceptance executed a real PowerShell (`pwsh`) stdout/stderr test successfully.

This becomes the expected future common boundary for FFmpeg/FFprobe and other subprocess-heavy capabilities.

### Automatic diagnostic report / support bundle

A normal first-party CLI execution creates automatically:

```text
<diagnostics-root>/<session-id>/
  session.json
  diagnostics.jsonl
  report.json
  report.md
  raw/
  support-bundle.zip
```

The Markdown report is a human-readable execution reconstruction containing:

- environment and execution identity;
- status/timing;
- executed nodes/steps and stages;
- batches/lots;
- system decisions;
- metrics/quality observations;
- anomalies/inconsistent results;
- subprocess/PowerShell outcomes;
- errors/failures;
- result/output summaries;
- Run Journal lifecycle;
- diagnostic hotspots/potential failure points derived only from recorded evidence;
- raw-log inventory.

The JSON report retains the machine-readable equivalent.

Core and JSON workflow CLIs enable diagnostics by default and expose:

```text
--diagnostics-dir <dir>
--no-diagnostics
```

Successful JSON output includes `diagnosticBundle`; handled failures print the bundle path before their classified exit code.

### Interruption / hard-crash evidence

Caught Ctrl+C/KeyboardInterrupt finalizes diagnostic status `INTERRUPTED` and returns code 130.

During execution, `session.json` starts as RUNNING and `diagnostics.jsonl` is append-written. If normal finalization never occurs, a stale session can later be packaged as `ABANDONED_OR_INTERRUPTED` while preserving the last durable evidence.

Fresh incomplete sessions are deliberately not auto-recovered because another live process could still own them. Stronger process/session ownership remains later work.

### Hosted evidence

Accepted implementation/test candidate:

`9c14e073ec5f770ce9d03d031c4ca1820bcd6ce2`

Primary implementation acceptance run:

`33556969496`

All five jobs passed:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow spike / Node.js 22.

Representative Ubuntu/Python 3.13 lane:

- **33 core tests — OK**;
- **59 JSON Node Pack tests — OK**;
- real PowerShell stdout/stderr diagnostic test — **OK**;
- core CLI diagnostic smoke — OK;
- real JSON workflow diagnostic smoke — OK;
- generated JSON artifact verification — OK.

Final memory/documentation closure checkpoint:

- SHA: `5e1e46714aaefe0827c96a415d7d58d57790a187`;
- GitHub Actions run: `33557338124`;
- result: **all five jobs success**.

M3 therefore has no remaining implementation or evidence gate.

## Architecture direction now

- `RunJournal` = durable lifecycle truth/history;
- `DiagnosticsSession` = richer forensic/support evidence;
- both correlate through run/workflow/node identity but remain separate injected concerns;
- support bundles are share-safe by default and do not claim automatic root cause;
- diagnostics is part of Definition of Done for new significant runtime/subprocess/integration capabilities;
- unfinished/stale evidence is never treated as automatic proof of process death;
- future cache/recovery decisions must emit diagnostic explanation.

## Active roadmap milestone — M4 Artifact Lifecycle + Recovery + Semantic Cache

Status: **ACTIVE TARGET / CLEARED TO IMPLEMENT**.

M4 must answer with executable evidence:

1. what makes an Artifact valid enough to reuse after restart;
2. how file existence/content changes invalidate reuse;
3. what exact input/config/node-version identity forms a safe cache signature;
4. which nodes are cacheable versus side-effectful;
5. how cached/recovered states extend M2 lifecycle truth;
6. how process/session ownership affects restart recovery;
7. how M3 diagnostics explains every reuse/invalidation/recovery decision.

Do not implement broad automatic resume from old `RUNNING`/successful rows without those rules.

## Later roadmap

After M4: official local Node Packs, imported application adapters, runtime/UI contract API, production workflow editor, ready-made Tools/Templates, desktop packaging, agent-first composition and release hardening.

## Next exact action

Create the dedicated M4 Artifact Lifecycle + Recovery + Semantic Cache spec and begin with persistent Artifact validity/provenance plus deterministic cache-signature acceptance tests before implementing automatic reuse.

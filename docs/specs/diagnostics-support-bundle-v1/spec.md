# Spec — Diagnostics + Support Bundle V1

Status: **RESOLVED / ACCEPTED**
Milestone: M3
Owner/implementer: ChatGPT Solo Development Mode

## Problem

Durable Execution V1 records lifecycle truth, but it is not sufficient to reconstruct every abnormal execution. It does not by itself capture arbitrary structured warnings, decisions, metrics, batch observations, subprocess stdout/stderr, tracebacks, quality degradation or a shareable end-of-run report.

K-Tools is moving toward FFmpeg, PowerShell, browsers, downloaders, AI/model calls and long-running local pipelines. Those boundaries need a common diagnostic contract before they proliferate.

## Delivered goal

M3 introduced a cross-cutting diagnostics contract that coexists with Run Journal, remains optional for low-level engine consumers, and generates a safe shareable support bundle after real first-party CLI execution.

## Core contracts delivered

### DiagnosticEvent

Ordered events carry:

- id/timestamp;
- severity;
- category/component;
- message;
- run/workflow/node/stage/batch correlation;
- JSON-safe context;
- optional exception type/message/traceback;
- LOG / DECISION / METRIC / BATCH / ANOMALY / EXCEPTION / SUBPROCESS / LIFECYCLE kind.

### DiagnosticsSession

A run-scoped collector/writer provides:

- append-written JSONL event stream;
- `session.json` RUNNING/terminal state;
- raw-log directory;
- safe normalization/redaction;
- explicit decision/metric/batch/anomaly helpers;
- exception capture;
- subprocess diagnostics;
- Markdown + JSON report generation;
- support-bundle ZIP generation.

### Subprocess diagnostics

The synchronous V1 wrapper retains redacted command identity, duration, exit code, stdout/stderr files, non-zero outcome, timeout and launch failure.

Interactive streaming subprocess control remains later work, but future FFmpeg/PowerShell/native capabilities have a common evidence boundary to build on.

## Report outputs delivered

```text
<diagnostics-root>/<session-id>/
  session.json
  diagnostics.jsonl
  report.json
  report.md
  raw/
    <subprocess>.stdout.log
    <subprocess>.stderr.log
  support-bundle.zip
```

The human report reconstructs environment, run identity/status/timing, executed nodes/steps, stages, batches/lots, decisions, metrics/quality observations, anomalies/inconsistent results, subprocess outcomes, errors, results/outputs, Run Journal lifecycle, diagnostic hotspots and raw-log inventory.

## Safe-sharing rules delivered

- recursive recognition/redaction of common credential/token/password/cookie/authorization patterns;
- secret command argument redaction;
- URL-query credential redaction;
- no wholesale environment-variable dump;
- conservative unknown-object serialization rather than arbitrary `repr()`/reflection;
- bounded structured strings;
- raw child-process text redacted before shareable bundle inclusion.

These controls reduce accidental leakage but do not claim perfect automatic recognition of every possible sensitive payload. Future adapters remain responsible for their own boundary review.

## CLI integration delivered

Core and JSON Node Pack workflow CLIs enable diagnostics by default and expose:

```text
--diagnostics-dir <directory>
--no-diagnostics
```

Normal success includes `diagnosticBundle` in JSON output. Handled validation/execution/unexpected errors finalize a bundle before their exit code. Caught `KeyboardInterrupt` finalizes diagnostic status `INTERRUPTED` and returns code 130.

## Run Journal integration

Run Journal remains lifecycle authority. Diagnostics supplements it.

Where both are enabled, the final report includes ordered journal events; diagnostics does not mutate journal state.

## Abnormal process-loss boundary

Evidence is written during execution, not only at finalization. If a process disappears, a stale incomplete session can later be packaged as `ABANDONED_OR_INTERRUPTED` through `recover_abandoned_sessions()`.

Fresh incomplete sessions are deliberately not auto-classified as abandoned. A stronger ownership/lease model remains later work.

## Acceptance

- [x] structured event model + JSON-safe safe-sharing normalization;
- [x] recursive secret-key/value redaction tests;
- [x] session writes state + JSONL + Markdown + JSON + ZIP;
- [x] exception type/message/traceback capture;
- [x] decision/metric/batch/anomaly helpers;
- [x] subprocess success/non-zero stdout/stderr/exit/duration evidence;
- [x] timeout and launch-failure representation;
- [x] real PowerShell stdout/stderr hosted smoke;
- [x] optional core engine diagnostic lifecycle observations;
- [x] core CLI automatic bundle on success/failure;
- [x] JSON Node Pack CLI automatic bundle on success/failure;
- [x] real `json.split` success/failure reports with workflow/node correlation;
- [x] seeded fake secrets absent from shareable report/event/raw outputs;
- [x] Ctrl+C diagnostic interruption semantics;
- [x] stale abandoned-session recovery with false-positive guard;
- [x] Windows/Linux hosted CI passes.

Hosted acceptance: run `33556969496` at SHA `9c14e073ec5f770ce9d03d031c4ca1820bcd6ce2` — all five jobs success; representative Ubuntu/Python 3.13 lane ran 33 core tests + 59 JSON tests and executed the real PowerShell smoke successfully.

## Non-goals retained

- automatic root-cause diagnosis;
- private chain-of-thought capture;
- OS crash dumps/minidumps;
- interactive terminal recording;
- unbounded binary payload capture;
- remote log shipping/telemetry;
- production GUI for log browsing;
- universal model-quality thresholds;
- process ownership leases / automatic resume.

Full evidence: `docs/specs/diagnostics-support-bundle-v1/evidence.md`.

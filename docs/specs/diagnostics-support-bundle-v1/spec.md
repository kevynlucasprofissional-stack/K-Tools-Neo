# Spec — Diagnostics + Support Bundle V1

Status: **ACTIVE**
Milestone: M3
Owner/implementer: ChatGPT Solo Development Mode

## Problem

Durable Execution V1 records lifecycle truth, but it is not yet sufficient to reconstruct every abnormal execution. It does not capture arbitrary structured warnings, decisions, metrics, batch-level observations, subprocess stdout/stderr, tracebacks, quality degradation or a shareable end-of-run report.

K-Tools is moving toward FFmpeg, PowerShell, browsers, downloaders, AI/model calls and long-running local pipelines. Those boundaries must become diagnosable before they proliferate.

## Goal

Introduce one cross-cutting diagnostics contract that can coexist with Run Journal, remain optional for low-level library consumers, and generate a safe shareable support bundle after a real execution.

## Core contracts

### DiagnosticEvent

Ordered event with:

- id;
- timestamp;
- severity;
- category;
- component;
- message;
- run/workflow/node/stage/batch correlation where known;
- JSON-safe context;
- optional exception fingerprint/traceback;
- event kind such as LOG, DECISION, METRIC, BATCH, ANOMALY, SUBPROCESS.

### DiagnosticsSession

A run-scoped collector/writer responsible for:

- JSONL structured event stream;
- raw-log directory;
- redaction/safe normalization;
- summary counters;
- report generation;
- support-bundle ZIP generation.

### Subprocess diagnostics

Reusable wrapper around `subprocess.run`/`Popen` semantics for bounded synchronous V1 execution. It must retain command identity, duration, exit code, stdout/stderr files and launch/timeout errors while redacting secrets from the report-facing command representation.

V1 need not solve interactive subprocesses or streaming progress yet; the contract must leave room for them.

## Report outputs

For a finalized session:

```text
<diagnostics-root>/<session-id>/
  diagnostics.jsonl
  report.json
  report.md
  raw/
    <subprocess>.stdout.log
    <subprocess>.stderr.log
  support-bundle.zip
```

The ZIP contains share-safe report/event/raw-log material produced by the session.

## Report reconstruction

The report should surface facts useful for a future debugging conversation:

- execution/session/run identity;
- product/Python/platform environment facts;
- start/end/duration/status;
- event counts by severity/kind;
- ordered decisions;
- batches/stages and reported counts;
- anomalies/warnings;
- errors and traceback fingerprints;
- subprocess outcomes;
- metrics and durations;
- output/result summaries when explicitly recorded;
- Run Journal event summary if provided to finalization;
- candidate diagnostic hotspots derived only from recorded warning/error/anomaly facts, not speculative root-cause claims.

## Redaction rules

Safe-sharing is the default.

Redact recursively when keys or command fragments indicate common secret classes, including token, api_key, password, secret, cookie, authorization/bearer, access/refresh keys and similar credential names.

Do not dump environment variables wholesale.

Unknown objects use conservative type-only metadata instead of arbitrary `repr()`.

Bound long strings in structured contexts; raw stdout/stderr may live in files but still pass basic secret-pattern redaction before inclusion in the safe bundle.

## CLI integration

Current first-party workflow CLIs should automatically create a Diagnostics Session by default and print/report the bundle path after completion.

Provide an explicit `--no-diagnostics` escape hatch for minimal/testing consumers and `--diagnostics-dir` to select the parent destination.

Diagnostics must finalize on success and on handled validation/execution failure.

## Run Journal integration

Run Journal remains lifecycle authority. Diagnostics supplements it.

Where both are enabled, final report may include summarized ordered journal events. Diagnostics must not replace or mutate journal state.

## Acceptance

- [ ] structured event model + JSON-safe safe-sharing normalization;
- [ ] recursive secret-key/value redaction tests;
- [ ] session writes JSONL + Markdown + JSON + ZIP;
- [ ] exception capture stores type/message/traceback safely;
- [ ] decision/metric/batch/anomaly helpers;
- [ ] subprocess success smoke captures stdout/stderr/exit/duration;
- [ ] subprocess non-zero and timeout/launch-failure paths are represented;
- [ ] core workflow engine can emit diagnostic lifecycle observations without requiring diagnostics;
- [ ] core CLI auto-generates bundle on success/failure;
- [ ] JSON Node Pack CLI auto-generates bundle on success/failure;
- [ ] real json.split success/failure report includes correlated workflow/node facts;
- [ ] seeded fake secrets are absent from shareable report/event/raw outputs;
- [ ] Windows/Linux hosted CI passes.

## Non-goals

- automatic root-cause diagnosis;
- private chain-of-thought capture;
- OS crash dumps/minidumps;
- interactive terminal recording;
- unbounded binary payload capture;
- remote log shipping/telemetry;
- production GUI for log browsing.

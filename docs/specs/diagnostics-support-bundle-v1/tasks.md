# Tasks — Diagnostics + Support Bundle V1

Status legend: `[ ]` pending, `[~]` active, `[x]` complete, `[!]` blocked.

## DG-001 — Structured diagnostics contract

- [x] severity and event-kind model;
- [x] run/workflow/node/stage/batch correlation;
- [x] JSON-safe structured context;
- [x] exception type/message/traceback capture;
- [x] decision, metric, batch and anomaly helpers.

## DG-002 — Safe sharing / redaction

- [x] recursive secret-key redaction;
- [x] inline token/password/authorization redaction;
- [x] URL query secret redaction;
- [x] command argument redaction;
- [x] no arbitrary unknown-object repr;
- [x] bounded structured strings;
- [x] seeded-secret regression tests.

## DG-003 — Subprocess / PowerShell diagnostics

- [x] subprocess start/end/duration/exit-code events;
- [x] stdout/stderr raw files;
- [x] non-zero exit representation;
- [x] timeout representation;
- [x] launch-failure representation;
- [x] raw output redaction;
- [x] real PowerShell stdout/stderr hosted smoke.

## DG-004 — Python logging bridge

- [x] stdlib logging handler;
- [x] level mapping;
- [x] logged exception capture;
- [x] safe LogRecord metadata only.

## DG-005 — Support bundle / report

- [x] `session.json` with RUNNING → terminal state;
- [x] `diagnostics.jsonl` ordered event stream;
- [x] `report.json` machine-readable reconstruction;
- [x] `report.md` human-readable reconstruction;
- [x] result summary;
- [x] node/stage/batch/decision/metric/anomaly/error/subprocess sections;
- [x] Run Journal lifecycle section;
- [x] raw-log inventory;
- [x] `support-bundle.zip`.

## DG-006 — Abnormal termination

- [x] explicit Ctrl+C/KeyboardInterrupt diagnostic finalization;
- [x] stale incomplete-session detection;
- [x] fresh-session false-positive protection;
- [x] recovered `ABANDONED_OR_INTERRUPTED` report;
- [x] recovered `session.json` terminalization;
- [x] recovered bundle idempotence.

## DG-007 — Real workflow/CLI integration

- [x] optional diagnostics injection into WorkflowEngine;
- [x] core CLI diagnostics enabled by default;
- [x] JSON Node Pack CLI diagnostics enabled by default;
- [x] `--diagnostics-dir`;
- [x] `--no-diagnostics` escape hatch;
- [x] real `json.split` success bundle;
- [x] validation-failure bundle;
- [x] real `json.split` execution-failure bundle;
- [x] Run Journal events attached when journal is enabled.

## DG-008 — Hosted evidence / closure

- [x] Windows/Linux hosted CI across Python 3.10/3.13;
- [x] record run `33556969496` and test counts in evidence;
- [x] update roadmap sequencing;
- [x] record architecture decisions;
- [x] update Testing policy;
- [x] update Engineering Journal;
- [~] final Current State / Roadmap promotion and documentation-head CI;

Implementation acceptance is complete. The only remaining closure gate is that the final memory-only HEAD retains the same green root CI before M4 code starts.

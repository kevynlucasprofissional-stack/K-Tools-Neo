# Evidence — Diagnostics + Support Bundle V1

Status: **IMPLEMENTATION COMPLETE / FINAL EXACT-HEAD HOSTED CLOSURE PENDING**

## Scope proved by repository tests

M3 introduces a support-grade diagnostic layer independent from, but correlated with, Durable Execution.

Primary implementation surfaces:

- `packages/ktools-core/src/ktools_core/diagnostics.py`;
- `packages/ktools-core/src/ktools_core/diagnostic_support.py`;
- `packages/ktools-core/src/ktools_core/engine.py`;
- `packages/ktools-core/src/ktools_core/cli.py`;
- `packages/ktools-json/src/ktools_json/cli.py`;
- core diagnostic/CLI tests;
- real JSON Node Pack CLI tests.

## Structured event evidence

Tests cover:

- DEBUG / INFO / WARNING / ERROR / CRITICAL severity model;
- LOG / DECISION / METRIC / BATCH / ANOMALY / EXCEPTION / SUBPROCESS / LIFECYCLE kinds;
- workflow/run/node correlation through real engine execution;
- optional diagnostics injection preserving diagnostics-free engine use;
- explicit decision reason/context;
- metric/unit observations;
- batch identifiers/count context;
- anomaly recording;
- exception type/message/traceback capture.

## Safe-sharing evidence

Regression tests seed fake secrets through several boundaries and require their values to be absent from shareable outputs:

- secret-like mapping keys;
- inline token/password/Authorization strings;
- URL query credentials;
- command argument values;
- unknown object `repr()`;
- logged exceptions;
- subprocess stdout.

The implementation does not snapshot environment variables wholesale and uses the existing conservative `to_json_safe` boundary for unknown runtime values.

This does not claim perfect recognition of every secret format. Future adapters remain responsible for avoiding/marking their own sensitive payloads.

## Subprocess / PowerShell evidence

The common subprocess diagnostic boundary records:

- start/completion;
- redacted command identity;
- cwd when supplied;
- duration;
- return code;
- stdout/stderr file paths and sizes;
- non-zero exit as an error observation;
- timeout exception;
- launch failure exception.

Raw captured text is redacted before becoming shareable support-bundle content.

A platform-conditional test executes `pwsh` or `powershell` when available and proves both stdout and stderr capture. Lanes without PowerShell skip that native-specific assertion rather than pretending the boundary was executed.

## Standard logging evidence

`DiagnosticLogHandler` bridges Python stdlib `logging` records to the active Diagnostics Session and records safe standard metadata without serializing arbitrary `LogRecord.__dict__` contents.

Tests cover normal warning logs and `logger.exception(...)`.

## Support-bundle evidence

Normal finalization creates:

```text
<diagnostics-root>/<session-id>/
  session.json
  diagnostics.jsonl
  report.json
  report.md
  raw/
  support-bundle.zip
```

`session.json` starts as `RUNNING` and is terminalized on normal finalization.

The human report has regression assertions for:

- environment;
- diagnostic hotspots / possible failure points;
- executed nodes / steps;
- stages;
- batches / lots;
- system decisions;
- metrics / quality observations;
- anomalies / inconsistent results;
- subprocess / PowerShell / external runtime events;
- errors / failures;
- result / outputs;
- Run Journal lifecycle;
- raw logs.

The machine report retains the complete structured reconstruction and event stream.

## Real CLI / Node Pack evidence

Both first-party workflow CLIs enable diagnostics by default and support:

```text
--diagnostics-dir <directory>
--no-diagnostics
```

Core CLI tests prove diagnostic output can coexist with SQLite Run Journal and that minimal consumers may explicitly opt out.

Real `ktools-json` tests prove:

- successful `json.literal -> json.split` execution produces a support bundle correlated to the real run and splitter node;
- Run Journal events are attached when SQLite journaling is also enabled;
- workflow validation failure produces a failure report/bundle;
- invalid real `json.split` configuration produces a FAILED bundle containing splitter-correlated error evidence.

## Interruption / crash evidence

### Ctrl+C / KeyboardInterrupt

CLI support explicitly classifies a caught `KeyboardInterrupt` as diagnostic status `INTERRUPTED`, returns conventional code 130 and finalizes a shareable bundle.

This does not itself promise that every underlying node/subprocess supports cooperative cancellation yet.

### Hard process loss

Diagnostic evidence is append-written during execution (`diagnostics.jsonl`) and session state begins as RUNNING.

`recover_abandoned_sessions()` can package a stale incomplete session as `ABANDONED_OR_INTERRUPTED`, preserve the last durable event and terminalize its `session.json`.

Fresh incomplete sessions are not recovered by default because another live process may still own them. Tests prove this false-positive guard and controlled explicit recovery.

No claim is made that staleness proves a specific crash cause.

## Diagnostic-hotspot evidence boundary

The support report may identify useful hotspots only from recorded WARNING / ERROR / ANOMALY evidence.

It does not perform automatic root-cause diagnosis and does not capture private chain-of-thought. Operational decisions may include concise runtime reason/evidence only.

## Hosted acceptance

Final exact-head hosted Windows/Linux evidence is intentionally pending while canonical M3 memory is synchronized.

Before M3 is promoted to RESOLVED, record here:

- final candidate/main SHA;
- GitHub Actions run ID;
- Ubuntu Python 3.10/3.13 results;
- Windows Python 3.10/3.13 results;
- xyflow-spike result;
- representative core/JSON test counts;
- PowerShell test execution/skip evidence by lane where visible.

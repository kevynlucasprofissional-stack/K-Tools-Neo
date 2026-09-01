# Evidence — Diagnostics + Support Bundle V1

Status: **ACCEPTED / RESOLVED — FINAL MEMORY HEAD RETAINS CI GATE**

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

The common subprocess diagnostic boundary records start/completion, redacted command identity, cwd, duration, return code, stdout/stderr files, non-zero exit, timeout and launch failure.

Raw captured text is redacted before becoming shareable support-bundle content.

The hosted Ubuntu 24.04 / Python 3.13 lane had `pwsh` available; the real PowerShell capture test executed rather than skipping and passed, proving both stdout and stderr capture on that native boundary.

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

The human report has regression assertions for environment, diagnostic hotspots, executed nodes/steps, stages, batches/lots, system decisions, metrics/quality observations, anomalies/inconsistent results, subprocess/PowerShell events, errors/failures, results/outputs, Run Journal lifecycle and raw logs.

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

The hosted core and JSON CLI smokes themselves emitted `diagnosticBundle` paths, proving automatic diagnostics at the real command boundary rather than tests calling only internal APIs.

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

Accepted hosted run:

- candidate/main SHA: `9c14e073ec5f770ce9d03d031c4ca1820bcd6ce2`;
- GitHub Actions run: `33556969496`;
- conclusion: **all five jobs success**.

Successful jobs:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow-spike / Ubuntu / Node.js 22.

Representative Ubuntu/Python 3.13 evidence:

- editable `ktools-core` install — success;
- editable `ktools-json` install — success;
- **33 core tests — OK**;
- **59 JSON Node Pack tests — OK**;
- PowerShell stdout/stderr test — **executed and OK**;
- core CLI smoke — success and emitted automatic `diagnosticBundle`;
- JSON workflow CLI smoke — success and emitted automatic `diagnosticBundle`;
- generated JSON artifact verification — success.

The other three Python matrix lanes reached and passed the same named install/test/CLI/artifact boundaries.

## Final closure rule

The subsequent milestone-memory commits are documentation-only relative to the accepted implementation/test tree. The repository still requires the final memory-closure HEAD to pass the same root CI before M4 implementation begins; that final run is recorded in `docs/CURRENT_STATE.md` once complete.

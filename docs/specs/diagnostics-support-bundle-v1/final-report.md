# Final Report — M3 Diagnostics + Support Bundle V1

## Terminal state

**RESOLVED / ACCEPTED.**

M3 establishes a first-class forensic/support layer for K-Tools Neo before cache/recovery, FFmpeg, browser, downloader and imported-app integration work expands the number of difficult failure boundaries.

## What changed

### Runtime diagnostics

`ktools-core` now exposes an optional `DiagnosticsSession` alongside the independent `RunJournal` contract.

The engine can correlate workflow/node start, success and failure observations with real run/workflow/node IDs without making diagnostics mandatory for library consumers.

### Structured evidence

The diagnostics contract supports:

- standard log events;
- explicit decisions and concise runtime reasons;
- metrics/quality observations;
- batches/lots;
- anomalies/inconsistent-result observations;
- exceptions/tracebacks;
- subprocess lifecycle and raw stdout/stderr;
- execution lifecycle facts.

### Shareable support bundle

A finalized session produces:

```text
session.json
diagnostics.jsonl
report.json
report.md
raw/
support-bundle.zip
```

`report.md` is designed to be sent directly for debugging. It includes environment and execution identity, steps/nodes, stages, batches, decisions, metrics, anomalies, subprocesses, errors, results, Run Journal lifecycle and recorded failure hotspots.

`report.json` preserves the machine-readable equivalent for deeper automated analysis.

### Native / PowerShell evidence

The common subprocess boundary captures command outcome, duration, exit code, stdout/stderr, timeout and launch failure. Command/report values pass safe-sharing redaction.

Hosted Ubuntu had PowerShell available and the real PowerShell stdout/stderr test executed successfully.

### Normal CLI behavior

Both current first-party workflow CLIs now create diagnostics automatically by default.

They support:

```text
--diagnostics-dir <directory>
--no-diagnostics
```

Successful `--json` responses include the `diagnosticBundle` path. Handled validation/execution/unexpected errors also finalize and print a bundle path before returning their classified exit code.

Caught Ctrl+C/KeyboardInterrupt becomes diagnostic status `INTERRUPTED` with code 130.

### Hard-crash evidence preservation

The system append-writes `diagnostics.jsonl` while work occurs and writes `session.json` as RUNNING at session start.

If normal finalization never occurs, stale sessions may later be recovered as `ABANDONED_OR_INTERRUPTED`, preserving the last durable evidence and creating a support bundle.

Fresh unfinished sessions are not auto-recovered because another live process might still own them.

## Security / privacy result

The diagnostics layer defaults toward safe sharing:

- common token/API-key/password/cookie/Authorization patterns are redacted;
- secret-like command arguments are redacted;
- unknown objects are not persisted using arbitrary repr/reflection;
- environment variables are not dumped wholesale;
- structured values are bounded;
- raw subprocess text is redacted before entering the shareable package.

Regression tests inject fake secrets through multiple boundaries and require them to be absent from support material.

This is defense-in-depth, not a promise that every conceivable secret format can be detected automatically.

## Evidence

Accepted implementation/test candidate:

`9c14e073ec5f770ce9d03d031c4ca1820bcd6ce2`

GitHub Actions:

`33556969496`

All jobs passed:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow spike / Node.js 22.

Representative Ubuntu/Python 3.13 lane:

- 33 core tests — OK;
- 59 JSON Node Pack tests — OK;
- PowerShell capture test — executed and OK;
- core CLI diagnostic smoke — OK;
- real JSON Node Pack diagnostic workflow smoke — OK;
- JSON output artifact validation — OK.

Detailed evidence: `evidence.md`.

## Architectural conclusions

1. Run Journal and Diagnostics are separate correlated concerns: lifecycle truth vs forensic/support evidence.
2. Diagnostics is now a prerequisite for new complex runtime/native/integration work.
3. Reports surface recorded facts and hotspots but do not manufacture root-cause certainty.
4. Diagnostic safe-sharing/redaction is an architectural invariant, not optional polish.
5. Abnormal-session recovery remains conservative until a stronger process ownership/lease model exists.

## Deferred boundaries

M3 does not claim:

- automatic root-cause diagnosis;
- automatic resume;
- semantic cache;
- process ownership leases;
- interactive subprocess streaming;
- production log viewer UI;
- OS minidumps;
- universal AI/model quality thresholds.

Those features build on this diagnostic foundation when their corresponding product milestones require them.

## Next milestone

M4 — **Artifact Lifecycle + Recovery + Semantic Cache**.

M4 must use the M2 durable identities and M3 diagnostics to explain why artifacts are valid/invalid, why cached work is reused or rejected, and why a recovery decision was made.

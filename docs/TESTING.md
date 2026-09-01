# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/adapter contracts.
4. CLI smoke — real headless workflow execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/PowerShell/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool → engine → capability → durable run/artifact/result/diagnostic bundle.

Do not promote evidence across levels.

A green job proves only the commands that job actually reached and completed.

## Root hosted CI

`.github/workflows/core-ci.yml` validates two surfaces.

### Python runtime + official JSON Node Pack

Matrix:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13.

Each matrix job performs:

1. checkout;
2. Python setup;
3. editable install of `packages/ktools-core`;
4. editable install of `packages/ktools-json`;
5. complete core unit/contract suite;
6. complete JSON Node Pack suite;
7. core CLI smoke;
8. JSON workflow CLI smoke;
9. generated JSON-part verification.

Because the suites are discovered from the repository, the matrix also exercises Durable Execution and Diagnostics/Support Bundle tests, including SQLite lifecycle, safe redaction, diagnostic report generation, subprocess timeout/launch failure, CLI support bundles and real `json.split` diagnostic success/failure behavior.

### xyflow spike

Ubuntu / Node.js 22 performs checkout, Node setup, `npm ci`, build, lint and deterministic Vitest tests.

This protects the audited spike from silent regression. It does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A claim that durable execution works requires:

- success lifecycle event ordering;
- handler/output-contract failure lifecycle;
- `WorkflowEngine(registry)` no-journal compatibility;
- SQLite write + close + reopen + query;
- persisted run/node terminal state;
- JSON-safe output metadata;
- explicit incomplete `RUNNING -> INTERRUPTED` reconciliation;
- real official Node Pack durable execution;
- Windows/Linux hosted regression.

Full resume/cache are separate claims and must not be inferred from interruption detection.

## Diagnostics + Support Bundle V1 evidence expectations

A diagnostics claim requires more than `print()` statements or a single exception log.

Minimum evidence includes:

- structured severity/kind/category/component fields;
- run/workflow/node correlation through real engine execution;
- decisions, metrics, batches and anomaly records;
- exception type/message/traceback capture;
- stdlib Python logging bridge;
- recursive credential-pattern redaction;
- command-argument redaction;
- unknown-object repr non-leakage;
- support-bundle creation containing `session.json`, `report.md`, `report.json`, `diagnostics.jsonl` and referenced raw logs;
- a human report that surfaces environment, executed steps, batches, decisions, metrics/quality observations, anomalies, subprocesses, errors, results and Run Journal lifecycle;
- real subprocess stdout/stderr + exit-code evidence;
- subprocess timeout and launch-failure evidence;
- PowerShell stdout/stderr smoke where PowerShell is present on the hosted/native lane;
- Ctrl+C/KeyboardInterrupt classification as `INTERRUPTED` at the CLI support boundary;
- stale incomplete-session recovery without classifying a fresh session as abandoned;
- a real official `json.split` success bundle and a real failure bundle;
- seeded fake secrets absent from report/event/raw shareable material;
- Windows/Linux hosted regression.

### Diagnostic evidence boundaries

A support bundle is **forensic evidence**, not proof of root cause. `diagnosticHotspots` may summarize recorded WARNING/ERROR/ANOMALY facts but must not be described as an automatic causal diagnosis.

A missing final report is not sufficient proof of a crash while a process might still be alive. Abandoned-session recovery must retain a staleness/ownership safety boundary until a stronger lease mechanism exists.

Low model accuracy or inconsistent domain results must be asserted by the domain capability/model adapter using explicit metric/anomaly records. The core diagnostics layer records the observation; it does not invent a universal quality threshold.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown custom objects.

Diagnostics intended for sharing additionally require redaction regression tests. Do not snapshot the complete environment-variable set or store credentials merely for convenience.

This does not mean every conceivable sensitive string can be recognized automatically. Callers must still explicitly mark/avoid highly sensitive payloads and future adapters must review their own boundaries.

## External/native boundaries

If a capability crosses a real external boundary (FFmpeg, PowerShell, browser, auth, subprocess application, OS integration), unit mocks alone are insufficient for claims about that boundary.

Use the lowest real boundary that proves the claim and record environment/version information where material. Future subprocess-heavy capabilities should use the common diagnostics boundary so failed native executions leave shareable evidence.

## Failure classification

A CI failure counts as product evidence only after the job reaches the corresponding boundary.

Examples:

- runner/billing failure before steps: platform/harness boundary;
- editable install failure: packaging boundary;
- unit test failure: code/contract boundary;
- CLI failure after passing unit tests: integration/runtime boundary;
- PowerShell/FFmpeg subprocess failure: native dependency boundary;
- support-bundle assertion failure: diagnostics/forensics boundary.

Do not change product code to fix a failure that never reached product code.

## Carry-forward policy

Evidence from a previous SHA may only be reused when the relevant code, tests and runtime boundary are shown to be equivalent.

Each major milestone records its exact candidate/head and hosted run IDs under its own `docs/specs/<milestone>/evidence.md` before being marked resolved.

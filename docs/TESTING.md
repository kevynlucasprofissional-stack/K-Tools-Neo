# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/adapter contracts.
4. CLI smoke — real headless workflow execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool → engine → capability → durable run/artifact/result.

Do not promote evidence across levels.

A green job proves only the commands that job actually reached and completed.

## Root hosted CI

`.github/workflows/core-ci.yml` currently validates two surfaces.

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

Because the test suites are discovered from the repository, this matrix also exercises Durable Execution V1 tests, including SQLite lifecycle/history/reconciliation, CLI `--journal`, and real `json.literal -> json.split` durable workflow behavior.

### xyflow spike

Ubuntu / Node.js 22 performs:

1. checkout;
2. Node setup;
3. `npm ci`;
4. build;
5. lint;
6. deterministic Vitest suite.

This protects the audited spike from silent regression. It does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A claim that durable execution works requires more than an in-memory event test.

Minimum evidence includes:

- success lifecycle event ordering;
- handler failure lifecycle;
- output-contract failure lifecycle;
- `WorkflowEngine(registry)` no-journal backward compatibility;
- SQLite write + close + reopen + query;
- persisted run/node terminal state;
- JSON-safe output metadata;
- explicit incomplete `RUNNING -> INTERRUPTED` reconciliation;
- a real official Node Pack workflow persisted through the same engine boundary;
- Windows/Linux hosted regression.

Full resume/cache are separate claims and must not be inferred from `INTERRUPTED` detection.

## Serialization/safety evidence

Journal metadata serialization must not use arbitrary `repr()` or introspection of unknown custom objects. The supported allow-list is tested; unknown values degrade to type-only non-serializable metadata.

This does not mean every possible error string or user-provided JSON field is non-sensitive. Callers should still treat run journals as local application data rather than public logs.

## External/native boundaries

If a capability crosses a real external boundary (FFmpeg, browser, auth, subprocess application, OS integration), unit mocks alone are insufficient for claims about that boundary.

Use the lowest real boundary that proves the claim and record environment/version information where material.

## Failure classification

A CI failure counts as product evidence only after the job reaches the corresponding checkout/install/test/runtime boundary.

Examples:

- runner/billing failure before steps: platform/harness boundary;
- editable install failure: packaging boundary;
- unit test failure: code/contract boundary;
- CLI failure after passing unit tests: integration/runtime boundary;
- FFmpeg subprocess failure: native dependency boundary.

Do not change product code to fix a failure that never reached product code.

## Carry-forward policy

Evidence from a previous SHA may only be reused when the relevant code, tests and runtime boundary are shown to be equivalent.

Each major milestone records its exact candidate/head and hosted run IDs under its own `docs/specs/<milestone>/evidence.md` before being marked resolved.

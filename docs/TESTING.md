# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated graph/model rules.
3. Contract tests — node/port/adapter contracts.
4. CLI smoke — real headless workflow execution boundary.
5. Integration tests — real adapters/subsystems exercised together.
6. Native smoke — Windows/FFmpeg/browser/subprocess boundary where required.
7. E2E — desktop editor → engine → capability → artifact/result.

Do not promote evidence across levels.

## Foundation baseline

Local sandbox evidence for the candidate:

```text
PYTHONPATH=packages/ktools-core/src python -m unittest discover -s packages/ktools-core/tests -v
=> 10 tests, OK

PYTHONPATH=packages/ktools-core/src python -m ktools_core packages/ktools-core/examples/hello-workflow.json --json
=> workflowId=hello-ktools; join.text="K-Tools Neo"; exit 0
```

A local editable-install attempt was not usable as product evidence because the execution sandbox had no network access to fetch build dependencies. This is classified as a harness/environment boundary, not a product failure.

## Root CI candidate

`.github/workflows/core-ci.yml` validates:

- Ubuntu and Windows;
- Python 3.11 and 3.13;
- editable package installation;
- unit/contract suite;
- CLI smoke.

Exact-SHA CI results must be recorded in `specs/platform-foundation/evidence.md` before promotion.

## Carry-forward policy

Evidence from a previous SHA may only be reused if the relevant code, test and runtime boundary are shown to be equivalent.

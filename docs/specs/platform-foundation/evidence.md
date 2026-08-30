# Evidence — Platform Foundation

## EV-001 — Local unit/contract suite

Environment: isolated Linux execution sandbox; source imported directly through `PYTHONPATH` because the sandbox blocks package-index network access.

Command:

```text
PYTHONPATH=packages/ktools-core/src python -m unittest discover -s packages/ktools-core/tests -v
```

Observed:

```text
10 tests
OK
```

Claims supported:

- typed DAG happy path;
- incompatible edge rejection;
- cycle rejection;
- missing required input rejection;
- unknown node/port rejection;
- duplicate target-input connection rejection;
- handler failure correlation to node ID;
- optional unconnected input execution;
- Artifact JSON round-trip.

Claims not supported: editable install, Windows behavior, GitHub CI, real media/adapters.

## EV-002 — Local CLI smoke

Command:

```text
PYTHONPATH=packages/ktools-core/src python -m ktools_core packages/ktools-core/examples/hello-workflow.json --json
```

Observed relevant payload:

```json
{"workflowId":"hello-ktools","nodeOutputs":{"join":{"text":"K-Tools Neo"}}}
```

Exit: 0.

Claim supported: headless CLI reaches the real workflow engine and executes the example DAG.

## EV-003 — Editable-install attempt in sandbox

Classification: HARNESS / ENVIRONMENT, not product failure.

Observed: pip build isolation attempted to reach the package index for setuptools and failed because the sandbox has no network/DNS access.

Follow-up evidence: direct-source tests and CLI smoke passed. Editable installation remains for GitHub CI.

## EV-004 — GitHub Actions run 33327645359

Candidate SHA: `3fb12310f531a3754c751116fdc5470ab29ea159`.

Observed:

- workflow was discovered and a four-job matrix was created;
- Windows 3.11, Windows 3.13, Ubuntu 3.11 and Ubuntu 3.13 all concluded `failure`;
- the jobs exposed no executed steps through the GitHub API;
- the job log endpoint returned `BlobNotFound` instead of product/build output.

Evidence boundary: GitHub Actions orchestration/job startup. No evidence shows that checkout, Python setup, package installation, tests or CLI smoke executed.

Claim supported: the workflow file is recognized by GitHub and matrix jobs are being scheduled.

Claim not supported: any K-Tools product/code failure. The first observable failure is before a recorded product step.

## EV-005 — Hardened exact-SHA GitHub Actions

Status: PENDING.

Material changes before retry:

- matrix aligned with declared Python support boundary: 3.10 and 3.13;
- workflow permissions explicitly restricted to `contents: read`;
- no path filter can hide a candidate-SHA validation run.

A second run is justified because the workflow definition materially changed. If the same pre-step fingerprint repeats, classify the runner/job-start boundary as externally blocked and do not repeat unchanged.

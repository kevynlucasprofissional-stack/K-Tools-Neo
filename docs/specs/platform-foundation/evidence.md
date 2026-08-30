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
- representative job log retrieval returned `BlobNotFound` instead of product/build output.

Evidence boundary: GitHub Actions orchestration/job startup. No evidence shows that checkout, Python setup, package installation, tests or CLI smoke executed.

## EV-005 — GitHub Actions run 33327842478 after material CI change

Candidate SHA: `4fdf578aee02051625462df85f1058d6882490d1`.

Material changes from EV-004:

- matrix aligned to declared Python support boundary: 3.10 and 3.13;
- workflow permissions explicitly restricted to `contents: read`;
- no path filter can hide candidate-SHA validation.

Observed:

- Ubuntu 3.10: `failure`;
- Ubuntu 3.13: `failure`;
- Windows 3.10: `failure`;
- Windows 3.13: `failure`;
- all four jobs again expose no executed steps;
- representative job `99301039366` returns an empty step list;
- representative log retrieval again returns `BlobNotFound`.

Classification: **same pre-product Actions/runner boundary as EV-004**.

Claim supported: changing Python matrix and workflow permissions did not move the first observable failure boundary.

Claim not supported: a defect in `ktools-core`, packaging, tests, Windows compatibility or Linux compatibility.

## EV-006 — GitHub UI proves historical billing/spending root cause

Source: user-provided screenshot of the GitHub Actions run annotations for the four matrix jobs.

Observed platform annotation:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings.
```

Classification: **PROVED EXTERNAL ACCOUNT/BILLING JOB-START FAILURE**.

Claims supported:

- the historical runs did not start because of GitHub account billing/spending state;
- historical red jobs are not evidence that K-Tools fails on Windows, Linux, Python 3.10 or Python 3.13;
- modifying K-Tools product code or the workflow implementation would not have fixed that boundary.

Material environment change after this evidence:

- repository changed from private to public;
- GitHub repository metadata now reports `visibility: public`.

Claim not yet supported:

- that the public-repository state is sufficient to let all current hosted jobs execute successfully.

Next discriminating evidence:

- a new exact-current-head PR run must reach Checkout, Setup Python, editable install, unit/contract tests and CLI smoke on Windows + Ubuntu.

## Promotion evidence status

`AC-007.1` remains **NOT YET SATISFIED** until the new exact-head CI runs through the product boundary and passes.

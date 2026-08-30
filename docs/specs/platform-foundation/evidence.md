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

## EV-006 — GitHub UI proves historical billing/spending root cause

Source: user-provided screenshot of the GitHub Actions run annotations for the four matrix jobs.

Observed platform annotation:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings.
```

Classification: **PROVED EXTERNAL ACCOUNT/BILLING JOB-START FAILURE**.

Material environment change after this evidence:

- repository changed from private to public;
- GitHub repository metadata reported `visibility: public`.

## EV-007 — Hosted Windows/Linux acceptance after environment change

Run: `33330660076`
Candidate SHA: `1ccffb11af25a8d993ead931183380d354746131`
Conclusion: `success`

Observed matrix:

- Ubuntu / Python 3.10: success;
- Ubuntu / Python 3.13: success;
- Windows / Python 3.10: success;
- Windows / Python 3.13: success.

Every matrix path passed Checkout, Setup Python, editable install, unit/contract tests and CLI smoke.

## EV-008 — Final exact-head promotion CI

Run: `33330801547`
Candidate SHA: `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7`
Conclusion: `success`

Observed matrix:

- Windows / Python 3.13: success;
- Ubuntu / Python 3.10: success;
- Ubuntu / Python 3.13: success;
- Windows / Python 3.10: success.

Every job passed:

1. Set up job;
2. Checkout;
3. Setup Python;
4. Install `ktools-core` editable;
5. Unit and contract tests;
6. CLI smoke;
7. cleanup / complete job.

Claim supported: the complete PR head including canonical memory, source study and multi-agent plan preserved the tested core behavior on hosted Windows and Ubuntu.

## EV-009 — Promotion to main

PR: `#1` — `feat(platform): establish typed workflow foundation`
Final PR head: `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7`
Merge method: squash
Promoted `main` commit: `bf6b5282a3df033a1394b05215a1ed97492a73c1`
Merged: yes

Pre-merge audit:

- PR mergeable;
- branch ahead of and not behind baseline `main`;
- final diff additive relative to the baseline;
- legacy GUI/loose utilities not rewritten;
- imported XCursos/YT-DLP app internals not modified;
- no second workflow engine introduced;
- final exact-head CI green on all four matrix jobs.

## Promotion evidence status

Platform Foundation promotion is **SATISFIED / RESOLVED**.

The next production claim must be established by a new spec: prove one real K-Tools capability through a single implementation owner usable directly and through a workflow Node Pack.

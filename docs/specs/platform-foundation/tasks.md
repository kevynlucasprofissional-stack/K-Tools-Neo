# Tasks — Platform Foundation

## TASK-001 — Establish canonical platform context
Status: VALIDATED

Requirements: REQ-008

Acceptance: AC-008.1

Result: `AGENTS.md`, constitution, constraints, current state, decisions, testing policy, known issues and Engineering Journal structure added.

Evidence: versioned files on candidate branch.

## TASK-002 — Implement typed node/workflow contracts
Status: VALIDATED

Requirements: REQ-001, REQ-002, REQ-004, REQ-006

Acceptance: AC-002.1, AC-002.2, AC-002.3, AC-004.1

Result: models, registry, type compatibility and Artifact serialization implemented with standard-library runtime only.

Evidence: 10-test local unit/contract suite plus audit regression coverage.

## TASK-003 — Implement deterministic DAG execution
Status: VALIDATED

Requirements: REQ-003

Acceptance: AC-003.1

Result: topological validation/execution and explicit validation/execution error classes implemented.

Evidence: unit suite returns `K-Tools Neo`; optional-input regression test added after audit finding.

## TASK-004 — Add headless CLI smoke path
Status: VALIDATED

Requirements: REQ-005

Acceptance: AC-005.1

Result: `python -m ktools_core <workflow.json> --json` executes the example workflow successfully in local harness.

## TASK-005 — Add and validate root CI
Status: BLOCKED

Requirements: REQ-007

Acceptance: AC-007.1

Implemented:

- root GitHub Actions workflow;
- Windows + Ubuntu matrix;
- Python 3.10 + 3.13 support-boundary checks;
- editable install, unit/contract and CLI smoke steps;
- least-privilege `contents: read`.

Blocked evidence:

- run `33327645359` / SHA `3fb12310...`: four jobs failed before recorded steps;
- run `33327842478` / SHA `4fdf578a...`: materially changed CI, same pre-step failure fingerprint;
- representative job step list is empty and log retrieval is `BlobNotFound`.

Next: resolve the external GitHub Actions job-start condition, then rerun this exact acceptance boundary.

## TASK-006 — Integration review and promotion decision
Status: VALIDATED

Requirements: all

Result:

- candidate diff is additive; legacy GUI, loose utilities and imported app internals are not modified by the platform foundation;
- local core tests/CLI are green;
- root CI acceptance is externally blocked before product execution;
- promotion decision: **DO NOT MERGE until TASK-005 becomes VALIDATED**.

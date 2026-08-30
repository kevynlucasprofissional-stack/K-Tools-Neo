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
Status: IN_PROGRESS / RETESTING AFTER MATERIAL ENVIRONMENT CHANGE

Requirements: REQ-007

Acceptance: AC-007.1

Implemented:

- root GitHub Actions workflow;
- Windows + Ubuntu matrix;
- Python 3.10 + 3.13 support-boundary checks;
- editable install, unit/contract and CLI smoke steps;
- least-privilege `contents: read`.

Historical blocked evidence:

- run `33327645359` / SHA `3fb12310...`: four jobs failed before recorded steps;
- run `33327842478` / SHA `4fdf578a...`: materially changed CI, same pre-step failure fingerprint;
- representative job step list was empty and log retrieval was `BlobNotFound`.

Root cause now proved by GitHub UI annotation:

- GitHub refused to start the jobs because of account payment/spending-limit state;
- therefore those red jobs do not evidence a K-Tools product failure.

Material environment change:

- repository changed from private to public;
- repository API confirms `visibility: public`.

Next evidence: new exact-head PR CI must actually reach checkout/install/test and pass on Windows + Ubuntu.

## TASK-006 — Integration review and promotion decision
Status: VALIDATED FOR HISTORICAL CANDIDATE / MUST RECHECK FINAL HEAD

Requirements: all

Historical result:

- candidate diff was additive; legacy GUI, loose utilities and imported app internals were not modified by the platform foundation;
- local core tests/CLI were green;
- historical root CI was externally blocked before product execution;
- prior promotion decision was correctly **DO NOT MERGE**.

Reopened condition:

Because the CI environment materially changed and architecture research was added to the PR, perform a final exact-head diff/audit after TASK-005 becomes green, then promote only if no material issue is found.

## TASK-007 — Study workflow-platform reference implementations
Status: VALIDATED

Objective: inspect the supplied n8n, Activepieces, LiteGraph.js, Rete.js, ComfyUI, Node-RED and xyflow source snapshots for architecture, UX, reuse boundaries and licensing implications.

Result:

- source-based study versioned at `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`;
- source snapshots are fingerprinted with SHA-256;
- reuse is classified as direct dependency / selective donor / clean-room reference;
- architecture recommendations cover Node Packs, Run Journal, semantic cache, subworkflows/tools, schema migrations and xyflow canvas integration;
- ADR-006/ADR-007 and Engineering Journal were synchronized.

Evidence: direct inspection of the supplied source archives and licenses; paths/hashes are recorded in the study.

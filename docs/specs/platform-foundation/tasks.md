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

Evidence: unit/contract suite.

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
Status: IN_PROGRESS

Requirements: REQ-007

Acceptance: AC-007.1

Result: root workflow defined for Windows/Ubuntu × Python 3.11/3.13.

Minimum evidence: exact candidate SHA successful CI jobs.

## TASK-006 — Integration review and promotion decision
Status: TODO

Requirements: all

Dependencies: TASK-005

Objective: inspect candidate diff, CI and docs for partial implementation, regression risk, ownership duplication or spec drift; update memory and only then promote.

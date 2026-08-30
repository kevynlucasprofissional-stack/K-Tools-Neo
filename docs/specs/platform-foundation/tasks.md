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
Status: VALIDATED

Requirements: REQ-007

Acceptance: AC-007.1

Implemented:

- root GitHub Actions workflow;
- Windows + Ubuntu matrix;
- Python 3.10 + 3.13 support-boundary checks;
- editable install, unit/contract and CLI smoke steps;
- least-privilege `contents: read`.

Historical blocker:

- runs `33327645359` and `33327842478` failed before recorded steps;
- GitHub UI proved the reason was account payment/spending-limit state;
- repository was subsequently changed from private to public.

Resolution evidence:

- run `33330660076` / SHA `1ccffb11af25a8d993ead931183380d354746131`: success;
- Ubuntu 3.10 + 3.13: success;
- Windows 3.10 + 3.13: success;
- all paths reached Checkout, Setup Python, editable install, unit/contract tests and CLI smoke successfully.

Result: AC-007.1 satisfied for the tested candidate.

## TASK-006 — Integration review and promotion decision
Status: IN_PROGRESS — FINAL EXACT-HEAD VALIDATION

Requirements: all

Completed review evidence:

- platform foundation remains additive relative to baseline;
- legacy GUI, loose utilities and imported app internals were not rewritten by the foundation;
- local core tests/CLI are green;
- hosted Windows/Linux CI is green on the validated candidate;
- workflow-platform research is versioned and architectural decisions synchronized;
- multi-agent ownership/protocol is versioned.

Remaining before merge:

1. finish memory closure files;
2. run CI on the exact final PR head;
3. inspect final diff/PR mergeability;
4. merge only if the final CI remains green and audit finds no material issue.

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

## TASK-008 — Establish multi-agent development operating model
Status: VALIDATED

Objective: define how ChatGPT, OpenCode and Antigravity can work concurrently without duplicated ownership or uncontrolled architectural drift, while explicitly keeping Codex out of this project's agent pool for now.

Result:

- `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` added;
- ChatGPT designated Conductor / Chief Architect / Integration Engineer;
- OpenCode designated Runtime / Backend Implementation Lead;
- Antigravity designated Frontend / UX / Product Prototype Lead;
- path/contract ownership map defined;
- branch/worktree and integration strategy defined;
- handoff contract and prompt templates defined;
- staged parallel waves defined from first real Node Pack through durable execution, UI, adapters, subflows and agent-first workflow generation;
- `AGENTS.md` and `docs/README.md` linked to the protocol.

Evidence: versioned coordination documents on PR #1 branch.

# Platform Foundation — Cycle Report

Status: **RESOLVED / PROMOTED TO MAIN**

## Objective

Create the smallest durable foundation for turning K-Tools Neo into one integrated product whose capabilities can be used both as ready-made tools and as composable workflow nodes.

## Initial state

`main` had the legacy integrated GUI, loose utilities and two imported app subtrees, but no shared workflow runtime, root CI, canonical platform spec set or Engineering Journal.

## Decisions

- one capability / one implementation owner;
- workflow runtime independent from visual editor;
- Python first for the core foundation;
- imported XCursos/YT-DLP apps remain bounded subsystems and future adapters call them rather than duplicate them;
- typed ports and Artifact provenance are core contracts;
- `@xyflow/react` is the preferred first canvas dependency, while `ktools-core` remains workflow truth;
- Run Journal + Artifact persistence are prioritized before broad production use of expensive media workflows;
- third-party implementations are classified by direct-dependency/selective-donor/clean-room reuse boundary before any code reuse.

## Implemented

- `packages/ktools-core`;
- typed workflow/node/edge/port models;
- node registry;
- deterministic DAG validation and execution;
- validation for unknown nodes/ports, duplicate target connections, missing required inputs, incompatible types and cycles;
- execution error correlation;
- optional-input semantics aligned between validation/execution;
- initial serializable `Artifact` model;
- headless JSON CLI and example workflow;
- 10-test unit/contract suite;
- root Windows/Ubuntu CI definition;
- root `.gitignore`;
- canonical engineering docs + Engineering Journal;
- source-based study of n8n, Activepieces, LiteGraph.js, Rete.js, ComfyUI, Node-RED and xyflow;
- multi-agent development protocol for ChatGPT, OpenCode and Antigravity, with Codex explicitly excluded from this project for now.

## Evidence

### Local source-path validation

- 10 tests PASS;
- CLI smoke PASS, producing `K-Tools Neo`.

### Historical GitHub Actions failure

- run `33327645359` failed before any recorded step;
- after material workflow hardening, run `33327842478` repeated the same pre-step fingerprint;
- GitHub UI annotation later proved the reason: account payment/spending-limit state prevented the jobs from starting.

Therefore those historical red runs were external Actions/account evidence, not K-Tools Windows/Linux failures.

### Material environment change

- repository changed from private to public;
- GitHub repository metadata confirmed `visibility: public`.

### Hosted acceptance after environment change

Run `33330660076` on SHA `1ccffb11af25a8d993ead931183380d354746131` concluded success.

- Ubuntu / Python 3.10: success;
- Ubuntu / Python 3.13: success;
- Windows / Python 3.10: success;
- Windows / Python 3.13: success.

Every path passed Checkout, Setup Python, editable installation, unit/contract tests and CLI smoke.

### Final exact-head promotion CI

Run `33330801547` on final PR head `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7` concluded success.

All four Windows/Ubuntu × Python 3.10/3.13 jobs passed the full workflow.

## Research / architecture evidence

`docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md` records the supplied-source analysis and snapshot fingerprints.

Key resulting direction:

- Node-RED: architectural reference for editor/runtime/registry and subflow concepts;
- Activepieces: reference for Pieces, durable execution and replay/skip patterns;
- ComfyUI: clean-room reference for expensive-pipeline validation/cache/progress;
- n8n: clean-room UX/contract reference rather than donor code;
- Rete.js/LiteGraph.js: targeted concepts, not competing graph ownership;
- xyflow: preferred MIT frontend canvas dependency.

## Multi-agent acceleration plan

`docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` establishes:

- ChatGPT — Conductor / Chief Architect / Integration Engineer;
- OpenCode — Runtime / Backend Implementation Lead;
- Antigravity — Frontend / UX / Product Prototype Lead;
- Codex — intentionally excluded from K-Tools for now;
- branch/worktree isolation;
- path/contract ownership;
- handoff protocol;
- staged parallel workstreams.

Immediate post-Foundation parallelism:

1. OpenCode: first real capability/Node Pack milestone;
2. Antigravity: isolated xyflow interaction spike against accepted fixture contracts;
3. ChatGPT: Conductor review/integration and specification of durable execution based on the first capability evidence.

## Regression / integration audit

The platform foundation is additive. The legacy K-Tools GUI, loose utility source files, XCursos Runner internals and YT-DLP TUI internals were intentionally not rewritten by this foundation implementation.

The research and multi-agent additions are documentation/decision artifacts and do not create a second workflow runtime.

Final audit before promotion confirmed:

- PR mergeable;
- branch ahead of and not behind baseline `main`;
- final exact-head CI green;
- no material out-of-scope code changes;
- no competing runtime ownership introduced.

## Promotion

PR #1: `feat(platform): establish typed workflow foundation`

- final PR head: `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7`;
- merge method: squash;
- promoted `main` commit: `bf6b5282a3df033a1394b05215a1ed97492a73c1`;
- merged successfully.

## Remaining risks / known gaps

- no real product utility node yet;
- no persistence/restart/cache;
- no production visual editor;
- no XCursos/YT-DLP adapters;
- no migration of legacy screens;
- root CI for imported apps remains future work;
- desktop-host choice/performance is not yet validated;
- future Node Pack schema/version migration still needs explicit design before third-party packs are supported.

## Final state

**RESOLVED.**

The Foundation milestone is promoted. The next production milestone must use a new spec to prove one real K-Tools capability through a single implementation owner usable directly and as a workflow Node Pack. The multi-agent plan may now be activated for parallel delivery under the documented ownership boundaries.

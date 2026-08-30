# Platform Foundation — Cycle Report

Status: **BLOCKED AT EXTERNAL CI PROMOTION GATE**

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
- visual editor technology remains deferred to a dedicated spike.

## Implemented

- `packages/ktools-core`;
- typed workflow/node/edge/port models;
- node registry;
- deterministic DAG validation and execution;
- validation for unknown nodes/ports, duplicate connections, missing required inputs, incompatible types and cycles;
- execution error correlation;
- optional-input semantics aligned between validation/execution;
- initial serializable `Artifact` model;
- headless JSON CLI and example workflow;
- 10-test unit/contract suite;
- root Windows/Ubuntu CI definition;
- root `.gitignore`;
- canonical engineering docs + Engineering Journal.

## Evidence

Local source-path validation:

- 10 tests PASS;
- CLI smoke PASS, producing `K-Tools Neo`.

GitHub Actions:

- run `33327645359` failed before any recorded step;
- after material workflow hardening, run `33327842478` repeated the same pre-step fingerprint;
- representative step list is empty and logs are unavailable as `BlobNotFound`.

Therefore the evidence does **not** support a claim that K-Tools failed on Windows/Linux. It supports a claim that the GitHub Actions job-start boundary is currently blocked before product execution.

## Regression / integration audit

The platform foundation is additive. The legacy K-Tools GUI, loose utility source files, XCursos Runner internals and YT-DLP TUI internals were intentionally not modified by the foundation implementation.

## Remaining risks / known gaps

- no real product utility node yet;
- no persistence/restart/cache;
- no visual editor;
- no XCursos/YT-DLP adapters;
- no migration of legacy screens;
- root CI for imported apps remains future work;
- exact-candidate CI acceptance is externally blocked.

## Promotion decision

**Do not merge PR #1.**

The smallest intervention required to resume is to inspect the failed GitHub Actions run in the repository UI, identify/resolve the platform-provided account/repository/runner job-start reason, and rerun PR #1. If the workflow then reaches an install/test step and fails, resume at that first product boundary.

## Exact resume point

1. resolve GitHub Actions job-start condition;
2. rerun PR #1;
3. require green Windows + Ubuntu acceptance;
4. update `evidence.md`, `tasks.md`, `CURRENT_STATE.md` and this report;
5. perform final exact-head audit;
6. only then merge/promote and begin the first real capability-node migration spec.

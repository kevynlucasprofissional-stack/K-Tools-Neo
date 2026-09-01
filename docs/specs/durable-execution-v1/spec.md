# Spec — Durable Execution V1

Status: **ACTIVE**
Milestone: M2
Owner/implementer: ChatGPT Solo Development Mode

## Problem

`WorkflowEngine` currently executes a validated DAG and returns outputs in memory, but once the process exits there is no durable record of:

- which run occurred;
- which nodes started/succeeded/failed;
- when each transition happened;
- which output metadata was produced;
- what error caused a failure;
- whether a previously running process disappeared before a clean terminal event.

The xyflow spike also proved that a production editor will need real runtime events rather than a simulated frontend state machine.

## Goal

Create a minimal durable execution layer that instruments the existing engine without making persistence mandatory for pure/headless users.

## Required behavior

### Event model

The runtime must emit an ordered logical journal of execution events:

- `RUN_STARTED`;
- `NODE_STARTED`;
- `NODE_SUCCEEDED`;
- `NODE_FAILED`;
- `RUN_SUCCEEDED`;
- `RUN_FAILED`;
- reconciliation event/state for an incomplete prior run when explicitly recovered.

Events contain stable run/workflow identity, timestamp and node identity when relevant.

### Status model

Run status must support at least:

- `RUNNING`;
- `SUCCEEDED`;
- `FAILED`;
- `INTERRUPTED`.

Node-run status must support the same relevant execution states.

`CANCELLED` is deferred until a real cancellation boundary exists.

### Optional engine instrumentation

Existing code that constructs `WorkflowEngine(registry)` must continue to work without SQLite or any journal configuration.

A caller may inject a journal implementation. When supplied, the engine records lifecycle events around real node execution.

### SQLite durability

Provide a stdlib SQLite implementation that persists:

- runs;
- node runs;
- journal events;
- JSON-safe output metadata;
- error type/message;
- start/end timestamps.

No third-party database dependency is required for V1.

### Query API

The SQLite implementation must allow callers to:

- list recent runs;
- fetch one run including node-run records;
- fetch journal events in order.

### Interruption observability

A persisted run left in `RUNNING` state because a process died must be reconcilable to `INTERRUPTED` on the next application/session recovery operation, distinct from a clean `FAILED` run.

V1 does not need automatic node resume.

### JSON-safe output persistence

Node outputs may include JSON primitives, mappings/sequences, enums, paths and `Artifact` values. The persistence boundary must convert supported values to JSON-safe data.

Unknown/non-serializable objects must not crash merely because output metadata is being journaled; preserve type information without unsafe arbitrary repr content.

## Real workload acceptance

At least one test must execute the real `ktools-json` `json.split` workflow with SQLite journaling and prove:

- run succeeded;
- both source and split nodes have durable terminal records;
- split output metadata is queryable after execution;
- generated files remain valid.

A failure workflow must prove node/run failure recording.

## Non-goals

- automatic resume/retry after interruption;
- semantic cache;
- remote/distributed workers;
- daemon/background service;
- production UI;
- cancellation API;
- durable storage of arbitrary large output payloads/blobs.

## Compatibility

- Python >=3.10;
- Windows and Linux hosted CI;
- existing Foundation API remains source-compatible for normal `WorkflowEngine(registry)` use;
- `ktools-json` remains a separate Node Pack and does not move business logic into core.

## Acceptance checklist

- [ ] journal/event/status model exists;
- [ ] in-memory journal exists for deterministic tests/basic consumers;
- [ ] SQLite journal/store exists using stdlib `sqlite3`;
- [ ] engine emits success lifecycle correctly;
- [ ] engine emits failure lifecycle correctly including output-contract failures;
- [ ] old engine construction works without journal;
- [ ] query API returns runs/nodes/events;
- [ ] JSON-safe conversion is deterministic enough for persisted metadata;
- [ ] interrupted-run reconciliation is tested;
- [ ] real `ktools-json` workflow is persisted/queryable;
- [ ] existing core + JSON + xyflow tests stay green;
- [ ] hosted CI on current main is green;
- [ ] Current State / Decisions / Testing / Journal are synchronized at closure.

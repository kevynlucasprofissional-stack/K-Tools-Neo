# Evidence — Durable Execution V1

Status: **CODE ACCEPTANCE PROVED; FINAL MEMORY-CLOSURE HEAD PENDING**

## Candidate identity

Durable execution implementation spans the M2 commits beginning after spec/task creation and is fully represented by code candidate:

`74325c1445c4622383d5da061184ca2d91fde70b`

Key implementation surfaces:

- `packages/ktools-core/src/ktools_core/journal.py`;
- `packages/ktools-core/src/ktools_core/sqlite_journal.py`;
- `packages/ktools-core/src/ktools_core/engine.py`;
- `packages/ktools-core/src/ktools_core/cli.py`;
- `packages/ktools-core/tests/test_journal.py`;
- `packages/ktools-core/tests/test_cli.py`;
- `packages/ktools-json/tests/test_durable_execution.py`;
- `packages/ktools-json/src/ktools_json/cli.py`;
- `packages/ktools-json/tests/test_cli.py`.

## Hosted acceptance run

GitHub Actions run: `33552906228`
Head SHA: `74325c1445c4622383d5da061184ca2d91fde70b`
Conclusion: **success**

All five jobs completed successfully:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13;
- xyflow spike / Ubuntu / Node.js 22.

Representative Ubuntu/Python 3.13 job proved:

- editable `ktools-core` install;
- editable `ktools-json` install;
- **20 core tests — OK**;
- **58 JSON Node Pack tests — OK**;
- core CLI smoke — success;
- JSON Node Pack workflow smoke — success;
- generated JSON artifact verification — success.

The same named boundaries passed on both Windows Python lanes and the other Ubuntu lane.

## Core lifecycle evidence

The new tests prove:

### Success

`MemoryRunJournal` observes the expected ordered lifecycle:

```text
RUN_STARTED
NODE_STARTED / NODE_SUCCEEDED ...
RUN_SUCCEEDED
```

Node success events retain JSON-safe output metadata.

### Handler failure

A node handler exception produces:

```text
RUN_STARTED
NODE_STARTED
NODE_FAILED
RUN_FAILED
```

while the public `WorkflowExecutionError` still identifies the failed node.

### Output-contract failure

A node returning unknown/invalid output shape also becomes durable `NODE_FAILED` + `RUN_FAILED` rather than escaping journal observability.

### Backward compatibility

`WorkflowEngine(registry)` with no journal remains valid and executes the original Foundation workflow.

## SQLite durability evidence

Tests prove:

- schema creation is idempotent through open/reopen;
- `RUN_STARTED` creates the durable run projection;
- node start/terminal events create/update node projections;
- events and projections are written transactionally per logical event;
- successful runs can be closed, journal connection reopened, and queried;
- run/node status and output metadata survive reopen;
- failures persist run/node error information;
- events are returned in durable SQLite sequence order;
- recent run listing and run detail lookup work;
- a manually persisted incomplete RUNNING run/node can be explicitly reconciled to `INTERRUPTED`;
- a second reconciliation is idempotent for already-terminal records.

## JSON-safe metadata boundary

Tests prove explicit support for:

- JSON primitives/mappings/sequences;
- K-Tools `Artifact`;
- enums;
- `Path`;
- dates/timestamps;
- finite and non-finite float normalization;
- deterministic set normalization;
- bytes represented as size/type metadata rather than persisted content.

An opaque custom object's `repr()` containing a fake token is **not** persisted. Unknown objects fall back to type-only non-serializable metadata.

## Real official Node Pack evidence

`test_real_json_workflow_is_queryable_after_success` executes:

```text
json.literal
    ↓
json.split
```

through a real `WorkflowEngine(..., journal=SQLiteRunJournal(...))`.

It proves:

- the run becomes `SUCCEEDED`;
- both nodes have durable `SUCCEEDED` records;
- `json.split` persisted output metadata includes summary and part records;
- closing and reopening the DB preserves the run/node detail;
- the two emitted JSON files parse and reconstruct the original ordered records.

`test_real_json_failure_is_durable_and_bound_to_splitter` proves an invalid real `json.split` mode results in:

- source node `SUCCEEDED`;
- splitter node `FAILED`;
- run `FAILED`;
- final ordered `NODE_FAILED`, `RUN_FAILED` events;
- no output directory produced by the invalid configuration path.

## CLI evidence

Both core and JSON CLIs support optional:

```text
--journal <sqlite-db>
```

Tests prove the CLI-created database can be reopened and queried for the emitted run ID.

This is not merely an internal persistence API; headless K-Tools execution can already opt into durable history.

## Interruption evidence boundary

M2 proves **detection/reconciliation**, not resume.

`reconcile_incomplete_runs()` is intentionally explicit instead of automatically firing on database open because another process could still own a RUNNING record.

No claim is made yet for:

- automatic restart/resume;
- replay-and-skip;
- semantic cache;
- cancellation;
- multi-process ownership leases;
- remote/distributed execution.

These belong to later milestones.

## Harness hardening after code acceptance

The hosted run produced deprecation warnings because older GitHub Action majors targeted Node 20 internally. After checking current official GitHub Action documentation, the root workflow was moved to the current v7 generation for checkout/setup-python/setup-node. That harness-only update must receive its own green hosted run before final M2 closure.

## Final closure requirement

Before changing status to RESOLVED:

1. the Actions-v7 head must complete green;
2. canonical Current State / Roadmap / Journal / Tasks must reflect M2 truth;
3. a final documentation-closure head must retain green hosted CI.

# Evidence — Durable Execution V1

Status: **RESOLVED / HOSTED ACCEPTANCE PROVED**

## Candidate identity

Durable execution implementation is fully represented by code candidate:

`74325c1445c4622383d5da061184ca2d91fde70b`

The subsequent harness hardening candidate is:

`4f1af103dff105807981f595be24cc7bf384f08c`

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

## Hosted code acceptance

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

## Harness hardening acceptance

The code-acceptance run showed GitHub runner warnings because the older `actions/checkout@v4` and `actions/setup-python@v5` action runtimes targeted deprecated Node 20 internally.

After checking current official GitHub Action documentation, the root workflow was moved to the v7 generation for:

- `actions/checkout`;
- `actions/setup-python`;
- `actions/setup-node`.

GitHub Actions run: `33553179743`
Head SHA: `4f1af103dff105807981f595be24cc7bf384f08c`
Conclusion: **success**

All five jobs again completed successfully, proving the harness update did not change the accepted product result.

## Core lifecycle evidence

The tests prove:

### Success

`MemoryRunJournal` observes the ordered lifecycle:

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

A node returning an invalid output contract also becomes durable `NODE_FAILED` + `RUN_FAILED` rather than escaping run observability.

### Backward compatibility

`WorkflowEngine(registry)` with no journal remains valid and executes the original Foundation workflow. Persistence is injected, not mandatory.

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
- a manually persisted incomplete `RUNNING` run/node can be explicitly reconciled to `INTERRUPTED`;
- a second reconciliation does not mutate already-terminal records.

## JSON-safe metadata boundary

Tests prove explicit support for:

- JSON primitives/mappings/sequences;
- K-Tools `Artifact`;
- enums;
- `Path`;
- dates/timestamps;
- finite and non-finite float normalization;
- deterministic set normalization;
- bytes represented as bounded size/type metadata rather than persisted content.

An opaque custom object's `repr()` containing a fake token is **not** persisted. Unknown objects fall back to qualified-type-only non-serializable metadata.

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
- closing and reopening the DB preserves run/node detail;
- emitted JSON files parse and reconstruct the original ordered records.

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

Tests prove a CLI-created database can be reopened and queried for the emitted run ID. Durable history is therefore accessible at a real headless product boundary, not only through internal classes.

## Interruption evidence boundary

M2 proves **detection/reconciliation**, not resume.

`reconcile_incomplete_runs()` is intentionally explicit instead of automatically firing on database open because another process could still legitimately own a `RUNNING` record.

No claim is made yet for:

- automatic restart/resume;
- replay-and-skip;
- semantic cache;
- cancellation;
- multi-process ownership leases;
- remote/distributed execution.

Those are later milestones and must build on this run/journal identity model rather than bypass it.

## Carry-forward to final memory closure

Commits after `4f1af103...` in this closure phase modify documentation/engineering memory only. Under the project's carry-forward policy, the product/harness evidence remains applicable because the tested implementation, test suites and workflow are unchanged. The final `main` head is still allowed to run hosted CI as an additional regression confirmation, but M2 product acceptance does not depend on pretending documentation changes altered the exercised runtime boundary.

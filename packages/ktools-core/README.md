# ktools-core

UI-independent workflow/runtime foundation for K-Tools Neo.

The package owns typed node contracts, workflow graphs, validation, deterministic DAG execution, the initial `Artifact` model and the first durable execution boundary.

## Run locally

```powershell
python -m pip install -e packages/ktools-core
python -m unittest discover -s packages/ktools-core/tests -v
python -m ktools_core packages/ktools-core/examples/hello-workflow.json --json
```

## Durable execution

Persistence is optional. Existing in-memory use remains valid:

```python
engine = WorkflowEngine(registry)
result = engine.execute(workflow)
```

To retain run/node lifecycle and JSON-safe output metadata in SQLite:

```python
from ktools_core import SQLiteRunJournal, WorkflowEngine

with SQLiteRunJournal("ktools-runs.sqlite3") as journal:
    result = WorkflowEngine(registry, journal=journal).execute(workflow)
    detail = journal.get_run_detail(result.run_id)
```

The headless CLI exposes the same capability:

```powershell
python -m ktools_core packages/ktools-core/examples/hello-workflow.json `
  --json `
  --journal .\ktools-runs.sqlite3
```

### Lifecycle events

Durable Execution V1 records an ordered logical event stream including:

- `RUN_STARTED`
- `NODE_STARTED`
- `NODE_SUCCEEDED`
- `NODE_FAILED`
- `RUN_SUCCEEDED`
- `RUN_FAILED`
- explicit `NODE_INTERRUPTED` / `RUN_INTERRUPTED` reconciliation events

Run/node projections can be queried through `SQLiteRunJournal.list_runs()`, `get_run()`, `get_node_runs()`, `get_events()` and `get_run_detail()`.

If a prior process disappeared while a run was still persisted as `RUNNING`, a later session may explicitly call:

```python
journal.reconcile_incomplete_runs()
```

This marks incomplete run/node records as `INTERRUPTED`. It deliberately does **not** resume execution.

### Output metadata safety

Journal payloads use a conservative JSON-safe converter. Standard JSON values, paths, dates/enums and explicit K-Tools `Artifact` values are normalized. Unknown custom objects are recorded only by type metadata instead of persisting arbitrary object `repr`/fields.

## Current built-in nodes

- `text.literal`
- `text.concat`
- `number.literal`
- `core.identity`

These are validation/runtime fixtures, not the final product palette. Real product capabilities live in official Node Packs such as `packages/ktools-json/`.

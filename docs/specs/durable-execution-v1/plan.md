# Plan — Durable Execution V1

## Strategy

Instrument the existing synchronous engine through a small injected journal contract rather than embedding SQLite directly into `WorkflowEngine`.

Preferred layering:

```text
WorkflowEngine
    |
    v
RunJournal protocol/contract
    |-------------------|
    v                   v
MemoryRunJournal    SQLiteRunJournal
                         |
                         v
                    sqlite3 file
```

This preserves headless/in-memory execution and gives the future UI a domain event model independent of database transport.

## Implementation sequence

1. Add `journal.py`:
   - lifecycle enums;
   - `RunEvent`;
   - JSON-safe value conversion;
   - `RunJournal` protocol;
   - `MemoryRunJournal`;
   - `NullRunJournal` or equivalent no-op behavior.
2. Add `sqlite_journal.py`:
   - schema bootstrap;
   - transactional event append;
   - derived `runs` / `node_runs` tables;
   - history/detail/event queries;
   - explicit incomplete-run reconciliation.
3. Instrument `WorkflowEngine`:
   - optional journal injection;
   - success lifecycle;
   - handler and output-contract failure lifecycle;
   - preserve original source compatibility.
4. Export public journal types from `ktools_core`.
5. Add core tests for:
   - event order;
   - failure order;
   - output-contract failure;
   - SQLite reopen/query;
   - JSON-safe conversion;
   - interrupted reconciliation;
   - default no-journal compatibility.
6. Add `ktools-json` real-workload integration test with SQLite journal.
7. Run hosted Actions matrix and inspect first failing boundary if red.
8. Refactor only after GREEN; avoid adding resume/cache prematurely.
9. Close evidence and canonical memory.

## Design constraints

- no third-party dependency for SQLite V1;
- journal timestamps use UTC ISO-8601 strings;
- event ordering in SQLite is defined by autoincrement sequence, not clock uniqueness;
- output metadata is JSON-safe, not a promise to persist arbitrary binary/large objects;
- journal failures are not silently swallowed when a journal is explicitly configured;
- validation failures occurring before a run begins remain validation errors rather than fake execution runs;
- node failures after `NODE_STARTED` must produce `NODE_FAILED` and `RUN_FAILED` before raising the public execution error, provided the journal itself remains available;
- interruption reconciliation is explicit/session-level in V1 to avoid incorrectly declaring another live process dead.

## Risks

1. Engine exception restructuring could accidentally change public error strings/types.
   - Mitigation: preserve existing `WorkflowExecutionError` contract and regressions.
2. SQLite derived-table updates could diverge from events.
   - Mitigation: append event and update derived rows in one transaction.
3. Persisting arbitrary outputs can fail JSON serialization.
   - Mitigation: controlled `to_json_safe` converter with non-serializable fallback metadata.
4. Reconciliation could be unsafe with concurrent processes.
   - Mitigation: explicit `reconcile_incomplete_runs()` rather than automatic constructor mutation.
5. Node handlers can create side effects before journal publication fails.
   - V1 policy: configured durable journal is part of the execution boundary; journal failure surfaces rather than pretending durability succeeded. Full transactionality over external side effects is out of scope.

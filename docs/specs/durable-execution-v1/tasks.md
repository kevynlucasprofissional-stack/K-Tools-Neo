# Tasks — Durable Execution V1

Status legend: `[ ]` pending, `[~]` active, `[x]` complete, `[!]` blocked.

## DE-001 — Event/status contract

- [~] define run/node lifecycle statuses;
- [ ] define ordered `RunEvent` structure;
- [ ] define JSON-safe output metadata conversion;
- [ ] add Memory/Null journal implementations.

## DE-002 — SQLite persistence

- [ ] bootstrap schema safely/idempotently;
- [ ] persist events + derived run records transactionally;
- [ ] persist node records/output metadata/errors;
- [ ] list/fetch run history;
- [ ] ordered event query;
- [ ] explicit interrupted-run reconciliation.

## DE-003 — Engine instrumentation

- [ ] optional journal injection preserving old constructor use;
- [ ] success event sequence;
- [ ] handler-failure event sequence;
- [ ] output-contract-failure event sequence;
- [ ] preserve public error behavior.

## DE-004 — Core evidence

- [ ] memory event-order tests;
- [ ] SQLite success/query/reopen tests;
- [ ] failure tests;
- [ ] reconciliation test;
- [ ] JSON-safe conversion tests;
- [ ] no-journal regression.

## DE-005 — Real Node Pack evidence

- [ ] execute real `json.literal -> json.split` through journaled engine;
- [ ] inspect persisted run + node outputs after execution;
- [ ] verify generated JSON artifacts;
- [ ] prove failure path with real pack where useful.

## DE-006 — Hosted integration

- [ ] exact-head GitHub Actions reaches all current core/json/xyflow boundaries;
- [ ] investigate/fix any material failure without weakening gates;
- [ ] record run ID / head SHA.

## DE-007 — Memory closure

- [ ] update `evidence.md`;
- [ ] update `docs/CURRENT_STATE.md`;
- [ ] update `docs/DECISIONS.md` if implementation evidence changes architecture;
- [ ] update `docs/TESTING.md` for durable-execution coverage;
- [ ] update Engineering Journal with reusable findings;
- [ ] mark M2 resolved only if acceptance is actually met;
- [ ] identify exact M3 entry point.

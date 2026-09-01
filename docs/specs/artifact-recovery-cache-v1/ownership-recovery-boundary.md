# M4 — Restart Recovery / Ownership Boundary

Status: **ACCEPTED V1 SAFETY BOUNDARY**

## What M4 means by recovery

M4 supports **safe recovery by starting a new run** and selectively reusing outputs from prior completed PURE node executions only when the semantic cache signature matches and every cached file Artifact remains strongly valid.

This is not the same thing as continuing an old in-flight run.

A restarted process may therefore:

1. create a new run id;
2. recompute the workflow graph normally;
3. reuse eligible completed node outputs as `NODE_CACHED` / `CACHED`;
4. execute every miss, invalid candidate, unsupported signature and side-effectful node normally.

The prior run remains historical truth. It is never rewritten to pretend the new run continued it.

## Why `RECOVERED` is not emitted in V1

An old `RUNNING` row is insufficient evidence that its owner is dead. Another process may still own it, the machine may have suspended, a PID may have been reused, or storage visibility may lag the actual process lifecycle.

M2 already preserves this distinction by requiring explicit reconciliation before projecting an incomplete run to `INTERRUPTED`.

M4 therefore does **not**:

- auto-resume old `RUNNING` nodes;
- claim old `SUCCEEDED` rows are cache entries;
- emit a `RECOVERED` node/run status;
- reclaim a run merely because a heartbeat timestamp looks old;
- infer process death from a stale diagnostics directory alone.

## Ownership evidence required before future automatic resume

A later resume implementation must define and test an atomic ownership/lease contract with at least:

- unique process/session owner id distinct from PID;
- boot/session identity sufficient to detect PID reuse/reboot;
- atomic acquire/renew/release semantics in persistent storage;
- explicit lease expiry policy;
- behavior under suspend/sleep, clock changes and delayed scheduling;
- crash/restart takeover rules;
- one-writer guarantees for side-effectful work;
- idempotency/replay contract per resumable node;
- evidence that a second live process cannot incorrectly steal an active run.

Until those properties are executable evidence, automatic in-flight resume is intentionally unavailable.

## Relation to semantic cache

Cache reuse is safer because it does not claim ownership of prior work. A cache entry is only a candidate result from a completed node execution. The new run independently validates:

- node type/version;
- normalized config;
- semantic inputs;
- explicit `CachePolicy.PURE` eligibility;
- cached output contract;
- current Artifact validity.

If any check fails, the candidate is discarded and the node executes normally.

## Relation to diagnostics

Every cache hit/miss/bypass/invalidation is a diagnostic decision. A restarted run therefore exposes why prior work was or was not reusable without inventing a resume narrative.

## Retention / deletion safety

M4 V1 owns **metadata**, not the user's output files.

- deleting a cache database is safe and only removes reusable metadata/results;
- deleting an Artifact-registry database only removes provenance observations;
- invalid cache entries may be removed from the cache database;
- K-Tools M4 does not automatically delete user file Artifacts;
- temporary/intermediate-file cleanup remains gated on a future explicit ownership/retention contract that can distinguish application-owned temporary data from user-owned results.

This deliberately favors orphaned metadata/temp files over accidental deletion of user data.

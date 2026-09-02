# ADR-026 — Text Split V1 preserves split-specific decode policy and publication semantics

Status: **ACCEPTED / PROVED IN M5 SLICE 4**

## Context

Text Merge and legacy Text Split both consume Markdown/TXT files but do not share the same decode fallback policy.

Merge is already canonical and uses its existing behavior. The legacy split path tries:

1. `utf-8-sig`;
2. `utf-8`;
3. `cp1252`;
4. `latin-1`.

A visual code-deduplication refactor could therefore silently change characters for byte sequences where cp1252 and latin-1 differ.

Text split also publishes multiple outputs. That introduces a different transaction boundary from single-output merge.

## Decision

### Decode policy

`ktools_text.splitter` owns the split-specific fallback order. Existing Text Merge decoding is not changed merely to share a helper.

Unification is allowed later only through a policy-driven abstraction whose tests prove both existing behaviors remain unchanged.

### Split owner

`splitter.split_text_file_into_parts(...)` is the canonical owner for decode, balanced planning, collision naming and multi-output publication orchestration.

Both the direct API and `text.split.parts` delegate to this owner. Workflow adapters do not implement split algorithms.

### Graph contract

`text.split.parts` uses:

```text
FILE -> FILE_SET
```

Version `1`, `CachePolicy.NEVER`.

The source is singular and remains singular. Output members are FILE Artifacts; no TEXT_FILE_SET/domain-specific collection type is introduced because FILE_SET already composes directly with `text.merge.files` and current graph-time requirements do not need stronger element typing.

### Publication policy

Every part is published atomically through Text-pack temp-then-replace behavior, but the whole output set is not transactional.

If a later part fails:

- earlier successfully published parts may remain;
- the failing destination is not left partial;
- temp residue for the failed publication is cleaned where practical;
- the failed operation does not return/record a successful complete output set.

### Cache consequence

`text.split.parts` remains NEVER because publishing the requested files is part of the operation. Repeated execution intentionally republishes and may select collision-safe new paths.

A PURE cached `file.literal` upstream may be reused without suppressing this required publication.

## Evidence

- spec gate `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / run `33656954591`;
- discriminating RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / run `33657352636`;
- GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / run `33657882057`;
- hosted hardened candidate `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / run `33660594733`, 5/5 including Text split→merge in every Python lane.

## Consequence for mixed Document Split

After this decision, both primitive branches used by the historical mixed Document Split have canonical owners:

- PDF -> `ktools-pdf`;
- Markdown/TXT -> `ktools-text`.

A future mixed Document Split slice should therefore be treated primarily as dispatch/orchestration + aggregation/error-contract work, not as permission to reimplement either split algorithm.

## Reopen conditions

Revisit only if:

- product requirements intentionally change decode semantics;
- a set-wide transaction/rollback requirement becomes real and safely implementable;
- graph-time element typing proves FILE_SET insufficient;
- a shared text-decoding abstraction can preserve caller-specific policy by contract.

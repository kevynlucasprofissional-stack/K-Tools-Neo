# Plan — Text Node Pack V1

Status: **IMPLEMENTATION COMPLETE / PROMOTION GATE**

## Phase 1 — characterize before extraction — COMPLETE

1. Pinned legacy behavior for decoding, merge bytes, suffix normalization and replacement.
2. Added failing characterization/contract tests.
3. Added failing FILE_SET core tests.

## Phase 2 — minimum core contract — COMPLETE

1. Added `DataType.FILE_SET` without inventing a collection class.
2. Kept V1 compatibility exact.
3. Regressed M0-M4 core behavior.
4. Added `files.literal` as the minimal ordered local-file source.

## Phase 3 — package owner — COMPLETE

1. Created `packages/ktools-text`.
2. Added classified Text merge error boundary.
3. Preserved legacy decoding order.
4. Added pure block/merged render surfaces.
5. Added streaming safe writer with same-directory temp publication.
6. Exposed direct API.

## Phase 4 — workflow adapter — COMPLETE

1. Registered `text.merge.files` with `files: FILE_SET -> file: FILE`.
2. Validated ordered Artifact input/local-file constraints.
3. Delegated to shared writer.
4. Returned current-run FILE Artifact.
5. Kept publication node `NEVER`.
6. Centralized `file:// URI → Path` interpretation in `ktools-core` after integration audit found duplicate logic.

## Phase 5 — evidence — CODE COMPLETE

1. Direct/node byte equivalence proved.
2. Repeated merge execution proved not cache-skipped.
3. ArtifactRegistry occurrence/strong snapshot proved.
4. `files.literal` cache validity/mutation invalidation proved.
5. Root CI installs/tests Text and runs a real text workflow smoke.
6. Accepted code candidate passed Windows/Linux Python 3.10/3.13 + xyflow.
7. Single-owner decision recorded: `ktools-text` is canonical; legacy GUI implementation is temporary compatibility debt.

## Remaining promotion sequence

1. Commit synchronized canonical memory.
2. Require exact-head hosted matrix green.
3. Mark PR #8 ready and perform final exact-head review.
4. Merge with expected-head guard.
5. Require post-merge `main` CI green.
6. Continue M5 with a new capability slice chosen from actual legacy ownership evidence.

# Plan — Text Node Pack V1

Status: **ACTIVE**

## Phase 1 — characterize before extraction

1. Pin legacy valid behavior for `read_text_with_fallback`, `merge_text_files`, output suffix normalization, separator bytes and output replacement.
2. Add failing characterization/contract tests in the new package.
3. Add failing core tests for FILE_SET type compatibility.

## Phase 2 — minimum core contract

1. Add `DataType.FILE_SET` only; do not invent a collection class.
2. Keep compatibility exact in V1.
3. Re-run all core tests including M4 semantic-cache list/Artifact behavior.

## Phase 3 — package owner

1. Create `ktools-text` packaging skeleton.
2. Implement small classified error taxonomy.
3. Implement decoding helper preserving legacy supported order.
4. Implement pure formatting/render owner.
5. Implement safe filesystem writer with same-directory temporary publication.
6. Expose direct API.

## Phase 4 — workflow adapter

1. Register `text.merge.files` with `files: FILE_SET -> file: FILE`.
2. Validate runtime Artifact sequence and local text-file constraints.
3. Delegate to the shared writer.
4. Return current-run output Artifact.
5. Mark node `NEVER`.

## Phase 5 — evidence

1. Prove direct/node byte equivalence.
2. Prove repeated node execution is not cache-skipped.
3. Prove ArtifactRegistry occurrence/strong snapshot.
4. Add root CI install/test + text workflow smoke.
5. Run hosted Windows/Linux matrix and xyflow.
6. Audit single-owner status and update canonical memory.

## Abort/reopen conditions

Reopen design before implementation if characterization shows the legacy function depends materially on hidden UI state or if FILE_SET requires broader covariance/runtime semantics than the current M4 container behavior can safely support.

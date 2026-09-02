# Plan — Text Split Node V1

Status: **ACTIVE / PRE-RED**

## Sequence

1. Characterize legacy split decode, line-balancing, naming, UTF-8 publication and collision semantics with tests that fail only because the new package contracts are absent.
2. Add pure `split_text_balanced` and the classified Text Split error boundary.
3. Add `split_text_file_into_parts` as the one decode/plan/publication owner.
4. Add a reusable Text-pack atomic content publisher only as needed; do not alter Text Merge semantics unless regression tests prove exact compatibility.
5. Extend direct API and `text.split.parts` adapter.
6. Prove FILE Artifact metadata/provenance + nested ArtifactRegistry snapshots.
7. Prove cached `file.literal` does not suppress NEVER split publication and repeated runs collision-safely create new outputs.
8. Add forced later-part publication failure test.
9. Prove direct/workflow byte equivalence and split→merge type composition.
10. Add hosted split→merge smoke to root CI.
11. Run integration audit for duplicate decoder/chunker/collision/publication logic and Text Merge regressions.
12. Close canonical memory only after exact-head 5-job CI is green.

## Key risk checks

- Do not unify Text Merge and Text Split decoding unless caller-specific policy is preserved.
- Do not treat Text Merge as an inverse of split; its separator behavior is independent.
- Do not introduce a specialized collection type.
- Do not claim set-wide transactionality.
- Do not start mixed Document Split until text split is canonical.

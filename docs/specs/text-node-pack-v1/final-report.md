# Final Report — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

## Objective

Extract the first low-coupling local legacy capability after M4 and prove that K-Tools can represent an ordered multi-file operation through the same capability owner for direct use and workflow use.

## Initial state

- Markdown/TXT merge lived in the large CustomTkinter monolith.
- The workflow type system had FILE but no honest ordered multi-file type.
- No official Text Node Pack existed.
- M4 cache/Artifact lifecycle was promoted and available as a prerequisite.

## Discovery and rejected alternatives

Markdown/TXT merge was compared with WebP→PNG and generic folder scanning. It won the first slice because it is stdlib-only and bounded. WebP→PNG brings Pillow/image-policy complexity; folder scan remains UI/callback coupled.

## Hypotheses and results

### H1 — an explicit FILE_SET is needed rather than smuggling file collections through JSON/ANY
Validated. Exact FILE_SET typing composes cleanly and did not require a collection object because existing M4 traversal already handles lists/tuples of Artifacts.

### H2 — files.literal can be PURE safely
Validated under M4 rules. The source node has no publication side effect, and cached FILE Artifacts are strongly revalidated. Source mutation forces execution rather than stale reuse.

### H3 — the merge publication node must remain NEVER
Validated. Equivalent runs must republish/replace the requested destination; a cached Artifact reference is not a substitute for the required side effect.

### H4 — direct Tool/API and workflow can share one owner
Validated. Both delegate to `writer.merge_text_files`, and equivalent executions are byte-identical.

### H5 — green behavior tests are sufficient to prove one-owner architecture
Refuted during integration review. A duplicate local-file URI parser existed across M4 and Text despite green behavior tests. It was centralized in `ktools-core` and regression-tested.

## Implemented

- `DataType.FILE_SET`;
- `files.literal`;
- `ktools_core.local_files.path_from_file_uri`;
- `packages/ktools-text` with capability, writer, API and node adapter;
- `text.merge.files: FILE_SET -> FILE`;
- legacy-compatible decoding/separator/publication behavior;
- first-class output Artifact provenance;
- M4 cache/ArtifactRegistry integration;
- hosted Text workflow smoke;
- ownership boundary making `ktools-text` canonical for future merge evolution.

## Evidence

RED: `1660a4dbac7efc7f21d7a96bfdebde8ffc13edd2`, run `33626957901`.

Intermediate accepted implementation candidate: `dbd39a1119ce1557d802a115404f01a3f797d93e`, run `33627879876`, five jobs success.

Final canonical-memory/promotion candidate: `31b02467cac9c9dc59733d32325728792eb83b22`, run `33629673452`, five jobs success.

Representative lane: 72 core + 64 JSON + 15 Text tests, all OK, followed by core/JSON/Text smokes.

Full evidence: `docs/specs/text-node-pack-v1/evidence.md`.

## Regression/audit

M0-M4 core contracts, official JSON Node Pack and xyflow spike remain green. The integration audit removed duplicated URI parsing rather than accepting test-green architectural drift.

## Ownership/debt

The old stable GUI still runs its historical merge implementation. It is no longer canonical, but it has not yet been physically redirected to the package. That wiring is deliberately deferred rather than hidden; new behavior must not be implemented in the legacy copy.

## Promotion

Draft PR #8 was closed administratively because the connected GitHub wrapper could not transition it from Draft to Ready.

Replacement non-draft PR #9 was opened from the exact same `m5-text-node-pack-v1` head and merged after the final hosted gate.

Promotion merge commit: `958d5bf563cda21673d69865d1508831c599c006`.

Post-merge `main` CI: run `33630159514`, **success**.

## Terminal state

**RESOLVIDO / PROMOVIDO.**

Text Node Pack V1 is part of `main`, its canonical ownership boundary is explicit, and post-merge hosted verification is green. M5 continues iteratively with Slice 2 discovery rather than reopening Slice 1.
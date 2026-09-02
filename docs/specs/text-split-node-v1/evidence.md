# Evidence — Text Split Node V1

Status: **RESOLVED / HOSTED EVIDENCE GREEN**

## Prerequisite gate

PDF Split V1 canonical closure:

- terminal HEAD `a26dfcee626eedc27366dfec93be68503343941a`;
- run `33656157870`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 3 was terminal-green before Slice 4 implementation began.

## Discovery and selection

Fresh discovery compared Text Split, mixed Document Split, Images→PDF, WebP→PNG and bounded Files/Folders work.

Text Split was selected because it is stdlib-only, reuses the established Text pack and FILE→FILE_SET contracts, has a clear legacy oracle, and removes the last primitive owner embedded inside future mixed Document Split. Images→PDF/WebP remain gated by a larger Pillow safety policy; Files/Folders remains a broader traversal/result-schema boundary.

## Legacy characterization preserved

- `.md` / `.txt` sources only;
- decode fallback order `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`;
- empty/whitespace-only content fails closed;
- line units use `splitlines(keepends=True)`;
- requested parts clamp to available line units;
- character-target balancing keeps lines indivisible and recomputes target after each chunk;
- whitespace-only chunks are filtered;
- output names use `{stem}_parte_XX_de_YY{lower_suffix}` with actual chunk count;
- existing/reserved names receive `_1`, `_2`, ... rather than overwrite;
- outputs are published as UTF-8;
- each output is temp-then-replace atomic, but the whole FILE_SET is not transactional;
- output order follows chunk order;
- progress is supplemental only.

Existing Text Merge decoding remains unchanged; its fallback policy is intentionally not unified with split merely for code deduplication.

## Spec gate

Commit `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` passed run `33656954591` 5/5 before RED.

## Discriminating RED

Commit `14a950d8d1b23412d7ba27dace66759d8ae2b37e`, run `33657352636`, failed intentionally at the new Text Split product contracts after bootstrap/prior suites reached their normal boundaries.

The RED required the missing pure planner, one-owner file splitter/direct API/node adapter and the new workflow contract rather than manufacturing a CI/package failure.

## GREEN

Commit `87558e8194692c045bdd95780fe05beb0f436e3a` implemented:

- `TextSplitError`;
- `split_text_balanced(...)` pure planner;
- split-specific decode fallback policy;
- `split_text_file_into_parts(...)` single implementation owner;
- reusable Text-pack atomic text-content publication;
- direct API + `text.split.parts` thin adapter;
- `text.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- output FILE Artifacts with MIME/provenance/chunk metadata;
- nested ArtifactRegistry strong snapshots;
- cached `file.literal` + required split re-publication proof;
- direct/workflow byte equivalence;
- ordered split→merge composition;
- forced later-part failure semantics.

Run `33657882057` passed Ubuntu/Windows Python 3.10/3.13 and xyflow.

## Hosted hardening candidate

Commit `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` added a real hosted:

```text
file.literal -> text.split.parts -> text.merge.files
```

smoke. The script writes a source document, executes the workflow, reopens all emitted parts, proves ordered concatenation reproduces the decoded source, then reopens/verifies downstream merge behavior.

Run `33660594733` passed all five jobs:

- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow-spike — success.

The new Text split→merge step itself completed successfully in every Python lane.

## Architectural evidence

Direct API and workflow node both delegate to `ktools_text.splitter.split_text_file_into_parts`; the adapter contains no decode fallback, line balancing, collision naming or publication algorithm.

`text.split.parts` remains NEVER because publication is required behavior. `file.literal` may be CACHED while split executes again and selects collision-safe new paths.

`FILE_SET` remains sufficient: the output members are first-class FILE Artifacts and compose directly into `text.merge.files`; no text-specific collection type is justified by current graph-time requirements.

## Failure boundary

Multi-output Text split is atomic per part, not all-or-nothing across the set. A forced second-part failure proves the first completed output may remain, the failing destination is absent, temporary residue is cleaned, and the failed operation does not return a successful output set.

## Promotion state

Technical acceptance is complete. Promotion requires only this synchronized memory-closure HEAD itself to remain green under the standard 5-job hosted gate.

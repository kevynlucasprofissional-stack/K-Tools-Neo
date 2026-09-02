# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/cache/artifact/adapter contracts.
4. CLI/workflow smoke — real headless execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/PowerShell/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool -> engine -> capability -> durable run/artifact/cache/result/diagnostic bundle.

Do not promote evidence across levels. A green job proves only the commands that job actually reached and completed.

## Root hosted CI

`.github/workflows/core-ci.yml` validates two surfaces.

### Python runtime + official JSON/Text/PDF Node Packs

Matrix:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13.

Each matrix job performs:

1. checkout;
2. Python setup;
3. editable install of `packages/ktools-core`;
4. editable install of `packages/ktools-json`;
5. editable install of `packages/ktools-text`;
6. editable install of `packages/ktools-pdf` plus declared dependencies;
7. complete core unit/contract suite;
8. complete JSON Node Pack suite;
9. complete Text Node Pack suite;
10. complete PDF Node Pack suite;
11. core CLI smoke;
12. JSON workflow CLI smoke + generated JSON-part verification;
13. Text merge workflow smoke + exact text Artifact verification;
14. Text split->merge workflow smoke that reopens ordered emitted chunks, proves clean concatenation reconstructs the source and verifies downstream merge behavior;
15. PDF merge workflow smoke + reopened page-order/dimension verification;
16. PDF split->merge workflow smoke that generates a five-page source, reopens three split parts to verify `2/2/1`, merges emitted Artifacts and reopens the recomposed PDF to verify original page order.

Because suites are discovered from the repository, the matrix also exercises Durable Execution, Diagnostics/Support Bundle and M4 Artifact/Cache contracts together, including SQLite lifecycle, safe redaction, support reports, subprocess failure boundaries, semantic cache reuse/invalidation and persistent Artifact observations.

### xyflow spike

Ubuntu / Node.js 22 performs checkout, Node setup, `npm ci`, build, lint and deterministic Vitest tests.

This protects the audited spike from silent regression. It does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A claim that durable execution works requires success lifecycle ordering; handler/output-contract failure lifecycle; no-journal compatibility; SQLite write/close/reopen/query; persisted run/node terminal state; JSON-safe output metadata; explicit incomplete `RUNNING -> INTERRUPTED` reconciliation; real official Node Pack execution; and Windows/Linux hosted regression.

Cache and automatic resume are separate claims and must not be inferred from interruption detection.

## Diagnostics + Support Bundle V1 evidence expectations

Minimum evidence includes structured severity/kind/category/component fields; run/workflow/node correlation; decisions, metrics, batches and anomalies; exception traceback; stdlib logging bridge; recursive redaction; command redaction; unknown-object non-leakage; support bundle creation; human report reconstruction; real subprocess stdout/stderr/exit code; timeout and launch-failure evidence; PowerShell where available; Ctrl+C classification; stale-session recovery; real Node Pack success/failure bundles; seeded secret non-leakage; and Windows/Linux hosted regression.

A support bundle is forensic evidence, not proof of root cause. `diagnosticHotspots` summarizes recorded facts rather than inventing causal certainty.

## Artifact Lifecycle + Semantic Cache V1 evidence expectations

A claim that a node result is safely reusable requires explicit PURE policy, deterministic semantic signature and valid outputs; previous success alone is insufficient.

For strong local-file reuse evidence, snapshot identity includes normalized file identity, size, mtime-ns, SHA-256 and observation time. Missing/change invalidates; same-size/restored-mtime mutation must still invalidate; unsupported directory/remote URI must fail closed. Content identity does not depend on random Artifact/run ids.

Persistent cache evidence requires close/reopen persistence, provenance, collision-safe serialization, Artifact rehydration/revalidation, explicit invalidation, failure normalization and fail-open workflow execution. A hit must prove the handler did not execute. Reused lifecycle is `RUN_STARTED -> NODE_CACHED -> RUN_SUCCEEDED`, with no fake `NODE_STARTED`. NEVER nodes always execute.

ArtifactRegistry evidence ties occurrences to current run/node/output port/value path, source EXECUTED/CACHED, original Artifact provenance and strong snapshot or explicit unsupported/error state. Historical observations remain queryable after filesystem mutation.

## Text Merge Node Pack V1 evidence expectations

A Markdown/TXT merge migration claim requires explicit ordered FILE_SET and exact FILE_SET compatibility; `files.literal` order + strong cache revalidation; UTF-8 BOM/UTF-8/latin-1 characterization; exact separator-mode bytes; order/suffix/collision/parent/temp-publication behavior; prior destination preservation on handled failure; direct API/node shared writer and byte equivalence; no duplicate local URI interpretation; `text.merge.files` NEVER with ArtifactRegistry proof; cached source without skipped publication; and hosted Windows/Linux exact-output smoke.

Final memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`.

## PDF Merge Node Pack V1 evidence expectations

A PDF merge migration claim requires explicit `pypdf` dependency; non-empty ordered PDF inputs; fail-closed protected/corrupt/zero-page handling; deterministic file->page order; `.pdf` suffix normalization; output/input collision rejection; same-directory temp publication; prior destination preservation on handled failure; semantic reopen equivalence; `pdf.merge.files: FILE_SET -> PDF` version 1 NEVER; one shared writer owner; PDF Artifact provenance/strong snapshot; cached source without skipped publication; and hosted Windows/Linux reopen smoke.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5.

## PDF Split Node V1 evidence expectations

A balanced PDF split migration claim requires `file.literal: -> FILE` PURE; single/multi file literals sharing local Artifact construction; source mutation invalidation; honest FILE/FILE_SET cardinality; `parts >= 2`; page-count clamp; balanced contiguous ranges; deterministic collision-safe names; fail-closed protected/corrupt/empty inputs; supplemental progress; per-part atomic publication; explicit later-part failure semantics; `pdf.split.parts: FILE -> FILE_SET` version 1 NEVER; PDF Artifact metadata/provenance; nested strong snapshots; one shared splitter owner; cached source without skipped publication; repeated collision-safe re-publication; direct/workflow equivalence; and hosted split->merge reopen proof.

Evidence chain: spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704` / `33652921999`; RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831`; GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159`; hardened candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424`, all hosted 5/5. Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` passed `33656157870` 5/5.

## Text Split Node V1 evidence expectations

A balanced Text split migration claim requires:

### Decode/planner semantics

- `.md` / `.txt` source validation;
- split-specific fallback order `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`;
- existing Text Merge decoder remains regression-green and is not silently changed;
- empty/whitespace-only input fails closed;
- `parts >= 2`, bool/non-integer rejected;
- line units remain indivisible;
- requested parts clamp to available line units;
- uneven line lengths are balanced by the characterized character-target algorithm;
- ordered clean chunks reconstruct the decoded normal source.

### Publication / Artifact contract

- clean names use `{stem}_parte_XX_de_YY{lower_suffix}` with actual output count;
- collisions choose `_1`, `_2`, ... rather than overwrite;
- outputs are UTF-8;
- each part uses Text-pack temp-then-replace publication;
- multi-output transaction boundary is explicit: earlier completed parts may remain after a later failure, while the failed destination is absent/clean;
- `text.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- every output member is a FILE Artifact with MIME/provenance/chunk metadata;
- ArtifactRegistry snapshots nested outputs strongly;
- cached `file.literal` may be reused while split still executes and republishes.

### Architecture / equivalence / composition

- pure `split_text_balanced` owner is directly tested;
- direct API and node delegate to `splitter.split_text_file_into_parts`;
- adapter contains no decoder, balancing, collision or publication algorithm;
- direct/workflow outputs are byte-identical in independent clean directories;
- hosted `file.literal -> text.split.parts -> text.merge.files` executes successfully and verifies both emitted chunks and downstream merge behavior on Ubuntu/Windows Python 3.10/3.13;
- xyflow remains green.

Evidence chain:

- spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / run `33656954591` — 5/5;
- RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / run `33657352636` — discriminating Text Split product failure;
- GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / run `33657882057` — 5/5;
- hardened candidate `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / run `33660594733` — 5/5 including Text split->merge smoke on every Python lane.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, do not continue old RUNNING work or emit RECOVERED; start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative for abandoned old runs.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Automatic cleanup of intermediate files requires later explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

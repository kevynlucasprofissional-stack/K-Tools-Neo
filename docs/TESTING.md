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

### Python runtime + official JSON/Text/PDF/Documents Node Packs

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
7. editable install of `packages/ktools-documents` after Text/PDF;
8. complete core unit/contract suite;
9. complete JSON Node Pack suite;
10. complete Text Node Pack suite;
11. complete PDF Node Pack suite;
12. complete Documents Node Pack suite;
13. core CLI smoke;
14. JSON workflow CLI smoke + generated JSON-part verification;
15. Text merge workflow smoke + exact text Artifact verification;
16. Text split->merge workflow smoke that reopens ordered emitted chunks, proves clean concatenation reconstructs the source and verifies downstream merge behavior;
17. PDF merge workflow smoke + reopened page-order/dimension verification;
18. PDF split->merge workflow smoke that generates a five-page source, reopens three split parts to verify `2/2/1`, merges emitted Artifacts and reopens the recomposed PDF to verify original page order;
19. Documents mixed split workflow smoke that creates real Markdown + PDF sources, filters an unsupported file, executes `files.literal -> document.split.files`, verifies report counts/types, reconstructs Text from emitted parts and reopens/verifies PDF page order/dimensions.

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

Evidence chain: spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704` / `33652921999`; RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831`; GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159`; hardened candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424`; terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870`, hosted 5/5.

## Text Split Node V1 evidence expectations

A balanced Text split migration claim requires split-specific `.md/.txt` decode characterization; `parts >= 2`; line-unit preservation/clamp/balancing; UTF-8 collision-safe atomic-per-output publication; explicit later-part failure semantics; `text.split.parts: FILE -> FILE_SET` v1 NEVER; FILE Artifact MIME/provenance/chunk metadata; nested strong snapshots; one canonical splitter owner; cached source without skipped publication; direct/workflow byte equivalence; and hosted split->merge proof in all Python lanes.

Evidence chain: spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`; RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`; GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`; hardened `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`; terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

## Mixed Document Split Orchestrator V1 evidence expectations

A mixed `.md/.txt/.pdf` orchestration migration claim requires all of the following.

### Batch behavior

- existing supported inputs only; unsupported/missing/non-files filtered before attempt;
- compatible source order preserved;
- `parts` integer >= 2, bool/non-integer rejected;
- `.md/.txt` dispatches to `ktools-text`; `.pdf` dispatches to `ktools-pdf`;
- each compatible source owns equal progress span `1/N` and child progress is clamped/mapped into that span;
- per-source exceptions are accumulated without aborting later sources;
- returned outputs flatten source order then child part order;
- at least one successful child result means node success with report errors;
- zero successful child results means classified batch failure;
- report includes input/output/error counts, error strings and normalized destination.

### Architecture

- `packages/ktools-documents` depends on core/text/pdf and introduces no new image/native dependency;
- direct API and workflow node delegate to one batch owner;
- batch owner calls `ktools_text.splitter.split_text_file_into_parts` and `ktools_pdf.splitter.split_pdf_into_parts` directly;
- documents pack contains no Text decoding/balancing, PDF reader/page-copy, primitive collision allocation or primitive atomic-writer algorithm;
- `document.split.files: FILE_SET -> FILE_SET + JSON`, version 1, `CachePolicy.NEVER`.

### Artifact/cache/persistence

- returned child Artifacts are preserved rather than reconstructed;
- PDF outputs remain PDF Artifacts with PDF metadata; Text outputs remain FILE Artifacts with Text metadata/MIME;
- current workflow `run_id/node_id` provenance is coherent;
- ArtifactRegistry snapshots every successfully returned flattened output;
- cached upstream `files.literal` may be reused while Documents still executes and republishes;
- repeated execution uses child collision-safe publication and does not become a Documents cache hit.

### Failure ownership

- child per-output atomic/non-transactional semantics remain explicit;
- earlier child outputs may exist on disk after a later child failure;
- when a child raises without returning those earlier outputs, Documents does not falsely include them in its successful FILE_SET;
- batch rollback/deletion is not inferred without ownership evidence.

### Hosted evidence

- spec gate `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`, 5/5;
- RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`, discriminating after Core/JSON/Text/PDF passed;
- GREEN/audited candidate `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`, 5/5;
- every Python lane installed Documents, ran its suite and passed the real mixed Text/PDF workflow smoke;
- xyflow remained green.

Final promotion additionally requires the synchronized memory-closure HEAD to pass the same five hosted jobs.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, do not continue old RUNNING work or emit RECOVERED; start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative for abandoned old runs.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Automatic cleanup of intermediate or orphaned published files requires later explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

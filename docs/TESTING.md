# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/cache/artifact/adapter contracts.
4. CLI/workflow smoke — real headless execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/PowerShell/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool → engine → capability → durable run/artifact/cache/result/diagnostic bundle.

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
13. Text workflow smoke + exact text Artifact verification;
14. PDF merge workflow smoke + reopened page-order/dimension verification;
15. PDF split→merge workflow smoke that generates a five-page source, reopens three split parts to verify `2/2/1`, merges emitted Artifacts and reopens the recomposed PDF to verify original page order.

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

### Artifact validity

For strong local-file reuse evidence:

- snapshot includes normalized file identity, size, mtime-ns, SHA-256 and observation time;
- unchanged file validates;
- missing file invalidates;
- size/mtime change invalidates quickly;
- same-size content mutation still invalidates when mtime is restored;
- change during hashing/validation fails closed;
- unsupported directory/remote URI is not mislabeled strongly valid;
- content identity does not depend on random Artifact/run ids.

### Semantic signature / cache lifecycle

Signature identity includes node type, implementation version, canonical config, semantic inputs and Artifact content identity where applicable. Equivalent mapping order must not change the signature; meaningful config/input/version/content changes must. Opaque values bypass cache rather than guess.

Persistent cache evidence requires close/reopen persistence, provenance, collision-safe serialization, Artifact rehydration/revalidation, explicit invalidation, failure normalization and fail-open workflow execution. A hit must prove the handler did not execute. Reused lifecycle is `RUN_STARTED -> NODE_CACHED -> RUN_SUCCEEDED`, with no fake `NODE_STARTED`. NEVER nodes always execute.

### Artifact registry

Persistent Artifact lifecycle evidence ties occurrences to current run/node/output port/value path, source EXECUTED/CACHED, original Artifact provenance and strong snapshot or explicit unsupported/error state. Historical observations remain queryable after filesystem mutation.

## Text Node Pack V1 evidence expectations

A Markdown/TXT merge migration claim requires:

- explicit ordered FILE_SET and exact FILE_SET compatibility;
- `files.literal` order + Artifact output + strong cache revalidation;
- UTF-8 BOM/UTF-8/latin-1 characterization;
- exact separator-mode bytes;
- order/suffix/collision/parent/temp-publication behavior;
- prior destination preservation on handled failure;
- direct API/node shared writer and byte equivalence;
- no duplicate local URI interpretation;
- `text.merge.files` NEVER with output Artifact provenance/ArtifactRegistry proof;
- cached source does not skip publication;
- hosted Windows/Linux package tests and exact-output Text workflow smoke.

Final memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`.

## PDF Merge Node Pack V1 evidence expectations

A PDF merge migration claim requires explicit `pypdf` dependency; non-empty ordered PDF inputs; fail-closed protected/corrupt/zero-page handling; deterministic file→page order; `.pdf` suffix normalization; output/input collision rejection; same-directory temp publication; prior destination preservation on handled failure; semantic reopen equivalence; `pdf.merge.files: FILE_SET -> PDF` version 1 NEVER; one shared writer owner; PDF Artifact provenance/strong snapshot; cached source without skipped publication; and hosted Windows/Linux reopen smoke.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5.

## PDF Split Node V1 evidence expectations

A balanced PDF split migration claim requires:

### Source/cardinality

- `file.literal: -> FILE`, version 1, PURE;
- single/multi file literals share local Artifact construction;
- source mutation invalidates cached file literal;
- `FILE` and `FILE_SET` are not silently interchanged.

### Split semantics

- one local PDF source;
- `parts >= 2`, bool/non-integer rejected;
- requested parts clamp to page count;
- balanced contiguous ranges, including `5 pages -> 3 parts = 2/2/1`;
- deterministic `{stem}_parte_XX_de_YY.pdf` clean names;
- existing/reserved names get `_1`, `_2`, ... rather than overwrite;
- protected/corrupt/empty inputs fail closed;
- progress callback is supplemental;
- each part is atomically published;
- later-part failure leaves no partial failed destination, while already completed parts may remain because V1 is not set-wide transactional.

### Platform integration

- `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- every output member is a PDF Artifact with current provenance, MIME and page-range metadata;
- ArtifactRegistry snapshots nested outputs strongly;
- direct API and node delegate to `splitter.split_pdf_into_parts`;
- adapter owns no page-partition/page-copy/collision/publication algorithm;
- cached `file.literal` may be reused while split still executes;
- repeated split collision-safely republishes.

### Composition

The strongest V1 integration oracle is:

```text
file.literal -> pdf.split.parts -> pdf.merge.files
```

The hosted smoke must reopen every part and the recomposed PDF. This proves `FILE -> FILE_SET -> PDF` composition and demonstrates that member-level PDF Artifact typing is sufficient without `PDF_SET` for the current use case.

Evidence chain:

- spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704` / run `33652921999`;
- RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / run `33653225831`;
- GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / run `33653824159`, 5/5;
- hardened candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / run `33654265424`, 5/5 including split→merge smoke on all four Python lanes.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, do not continue old RUNNING work or emit RECOVERED; start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative for abandoned old runs.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Automatic cleanup of intermediate files requires later explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

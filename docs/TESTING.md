# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/cache/artifact/adapter contracts.
4. CLI smoke — real headless workflow execution boundary.
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
14. PDF workflow smoke + reopened page-order/dimension verification.

Because suites are discovered from the repository, the matrix exercises Durable Execution, Diagnostics/Support Bundle and M4 Artifact/Cache contracts together, including SQLite lifecycle, safe redaction, support reports, subprocess failure boundaries, semantic cache reuse/invalidation and persistent Artifact observations. M5 additionally exercises FILE_SET, Text and PDF publication semantics.

### xyflow spike

Ubuntu / Node.js 22 performs checkout, Node setup, `npm ci`, build, lint and deterministic Vitest tests.

This protects the audited spike from silent regression. It does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A claim that durable execution works requires:

- success lifecycle event ordering;
- handler/output-contract failure lifecycle;
- `WorkflowEngine(registry)` no-journal compatibility;
- SQLite write + close + reopen + query;
- persisted run/node terminal state;
- JSON-safe output metadata;
- explicit incomplete `RUNNING -> INTERRUPTED` reconciliation;
- real official Node Pack durable execution;
- Windows/Linux hosted regression.

Cache and automatic resume are separate claims and must not be inferred from interruption detection.

## Diagnostics + Support Bundle V1 evidence expectations

A diagnostics claim requires more than `print()` statements or a single exception log.

Minimum evidence includes structured severity/kind/category/component fields; run/workflow/node correlation; decisions, metrics, batches and anomalies; exception traceback; stdlib logging bridge; recursive redaction; command redaction; unknown-object non-leakage; support bundle creation; human report reconstruction; real subprocess stdout/stderr/exit code; timeout and launch-failure evidence; PowerShell where available; Ctrl+C classification; stale-session recovery; real Node Pack success/failure bundles; seeded secret non-leakage; and Windows/Linux hosted regression.

A support bundle is forensic evidence, not proof of root cause. `diagnosticHotspots` summarizes recorded facts rather than inventing causal certainty. Low model accuracy/inconsistent domain results must be asserted by the domain capability using explicit metrics/anomalies; core diagnostics records the observation rather than inventing a universal threshold.

## Artifact Lifecycle + Semantic Cache V1 evidence expectations

A claim that a node result is safely reusable requires explicit PURE policy, deterministic semantic signature and valid outputs; previous success alone is insufficient.

### Artifact validity

For strong local-file reuse evidence:

- snapshot includes normalized file identity, size, mtime-ns, SHA-256 and observation time;
- unchanged file validates;
- missing file invalidates;
- size/mtime change invalidates quickly;
- same-size content mutation must still invalidate when mtime is restored;
- change during hashing/validation fails closed;
- unsupported directory/remote URI is not mislabeled strongly valid;
- content identity does not depend on random Artifact/run ids.

### Semantic signature

Signature identity includes node type, implementation version, canonical config, semantic inputs and Artifact content identity where applicable. Equivalent mapping order must not change the signature; meaningful config/input/version/content changes must. Opaque/nondeterministic values bypass cache rather than guess.

### Persistent cache / lifecycle truth

Persistent cache evidence requires close/reopen persistence, provenance, collision-safe serialization, Artifact rehydration/revalidation, explicit invalidation, failure normalization and fail-open workflow execution. A hit must prove the handler did not execute. Reused lifecycle is `RUN_STARTED -> NODE_CACHED -> RUN_SUCCEEDED`, with no fake `NODE_STARTED`. NEVER nodes always execute.

### Artifact registry

Persistent Artifact lifecycle evidence ties occurrences to current run/node/output port/value path, source EXECUTED/CACHED, original Artifact provenance and strong snapshot or explicit unsupported/error state. Historical observations remain queryable after filesystem mutation.

### Real workload

M4 acceptance includes both `json.split.plan` as real PURE reusable computation and `json.split` as side-effectful NEVER publication.

## Text Node Pack V1 evidence expectations

A Markdown/TXT merge migration claim requires:

- explicit ordered FILE_SET and exact FILE_SET compatibility;
- `files.literal` order + Artifact output + strong cache revalidation;
- UTF-8 BOM/UTF-8/latin-1 characterization;
- exact `completo`, `simples`, `nenhum` bytes;
- order/suffix/collision/parent/temp-publication behavior;
- prior destination preservation on handled failure;
- direct API/node shared writer and byte equivalence;
- no duplicate local URI interpretation;
- `text.merge.files` NEVER with output Artifact provenance/ArtifactRegistry proof;
- cached source does not skip publication;
- hosted Windows/Linux package tests and exact-output Text workflow smoke.

Final memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed run `33631040505`.

## PDF Merge Node Pack V1 evidence expectations

A PDF merge migration claim requires:

### Dependency and input boundary

- `ktools-pdf` declares `pypdf` explicitly; execution code never auto-installs it;
- input is a non-empty ordered sequence rather than one path accidentally iterated as text;
- every path exists, is a file and uses `.pdf`;
- local Artifact URI parsing reuses `ktools-core`;
- encrypted/protected, corrupt/unreadable and zero-page PDFs fail closed with domain-classified error.

### Semantic merge/publication

- file order then page order is deterministic;
- output suffix normalizes to `.pdf`;
- output cannot be one of the inputs;
- same-directory temp output precedes final replace;
- prior destination survives handled failure before replacement;
- successful complete publication may replace an existing non-input destination;
- direct progress callback remains available but owns no semantics;
- PDF semantic equivalence is proved by reopened page structure/order rather than requiring incidental binary identity.

### Platform integration

- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- direct API and node delegate to `writer.merge_pdf_files`;
- adapter contains no reader/page-copy/publication algorithm;
- output is a PDF Artifact with current run/node provenance and useful page/source metadata;
- ArtifactRegistry records EXECUTED output + strong snapshot;
- cached `files.literal` may be reused while PDF merge republishes.

### Hosted evidence

RED `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`, reached PDF tests after package/dependency and all prior suites passed.

Accepted technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491`, passed Ubuntu/Windows Python 3.10/3.13 and xyflow. The real PDF smoke generates source PDFs, executes the workflow, reopens `merged.pdf` and verifies ordered page dimensions `(101x201, 102x202, 301x401)` in every Python lane.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, do not continue old RUNNING work or emit RECOVERED; start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative for abandoned old runs.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Automatic cleanup of intermediate files requires later explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

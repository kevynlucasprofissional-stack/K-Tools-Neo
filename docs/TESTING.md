# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/cache/artifact/adapter contracts.
4. CLI/workflow smoke — real headless workflow execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/PowerShell/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool → engine → capability → durable run/artifact/cache/result/diagnostic bundle.

Do not promote evidence across levels. A green job proves only the commands that job actually reached and completed.

## Root hosted CI

`.github/workflows/core-ci.yml` validates the Python platform/official Node Packs and the xyflow spike.

### Python runtime + official JSON/Text Node Packs

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
6. complete core unit/contract suite;
7. complete JSON Node Pack suite;
8. complete Text Node Pack suite;
9. core CLI smoke;
10. JSON workflow smoke;
11. generated JSON-part verification;
12. Text workflow smoke;
13. exact generated merged-text verification.

Because suites are discovered from the repository, the matrix exercises Durable Execution, Diagnostics/Support Bundle, M4 Artifact/Cache contracts, FILE_SET and both official Node Packs together.

### xyflow spike

Ubuntu / Node.js 22 performs checkout, Node setup, `npm ci`, build, lint and deterministic Vitest tests.

This protects the audited spike from silent regression. It does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A claim that durable execution works requires success lifecycle event ordering, handler/output-contract failure lifecycle, no-journal compatibility, SQLite write/close/reopen/query, persisted terminal states, JSON-safe output metadata, explicit incomplete RUNNING→INTERRUPTED reconciliation, real official Node Pack durable execution and Windows/Linux hosted regression.

Cache and automatic resume are separate claims and must not be inferred from interruption detection.

## Diagnostics + Support Bundle V1 evidence expectations

A diagnostics claim requires structured severity/kind/category/component fields; run/workflow/node correlation; decisions/metrics/batches/anomalies; exception/traceback capture; stdlib logging bridge; recursive secret redaction; command redaction; unknown-object repr non-leakage; support-bundle creation; report reconstruction; real subprocess evidence; timeout/launch-failure evidence; PowerShell smoke where present; Ctrl+C classification; stale-session recovery; real Node Pack success/failure bundles; seeded-secret non-leakage; and Windows/Linux hosted regression.

A support bundle is forensic evidence, not proof of root cause. `diagnosticHotspots` summarizes recorded observations rather than causal certainty.

## Artifact Lifecycle + Semantic Cache V1 evidence expectations

A claim that a node result is safely reusable requires explicit cacheability plus semantic identity plus valid reusable outputs. Previous success alone is insufficient.

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

### Semantic signature

Tests must prove node type/version, canonical config, semantic inputs and applicable Artifact content identity participate in signatures. Equivalent JSON mapping order must not change identity; config/input/version/content changes must. Opaque values bypass cache rather than guess.

### Persistent cache

Requires close/reopen persistence, provenance, collision-safe serialization, supported Artifact rehydration/revalidation, invalidation/removal behavior, store-error normalization and fail-open workflow behavior.

### Engine lifecycle truth

A real hit proves the handler did not execute. Journal semantics for a reused node include `NODE_CACHED` without fake `NODE_STARTED`; a `NEVER` node always executes.

### Artifact registry

Persistent records bind current run/node/output/value path, EXECUTED/CACHED source, original Artifact provenance and strong snapshot or explicit unsupported/error state. Historical snapshots remain queryable after current filesystem mutation.

### Real workload

Fixture nodes are insufficient for milestone promotion. M4 proves a real PURE `json.split.plan` workload and a side-effectful `json.split` that must republish.

## Text Node Pack V1 evidence expectations

A local multi-file Text capability is promoted only when all applicable layers are proved:

### FILE_SET

- explicit ordered FILE_SET type exists;
- FILE and FILE_SET are not interchangeable;
- configured order survives source→edge→consumer;
- source outputs are first-class FILE Artifacts;
- cached source results are revalidated against real files and source mutation forces execution.

### Characterized merge behavior

- UTF-8 BOM, UTF-8 and latin-1 decoding order matches the supported legacy contract;
- `completo`, `simples` and `nenhum` bytes are characterized;
- input order and output suffix normalization are proved;
- output/input collision is rejected;
- same-directory temporary publication prevents partial replacement;
- an existing non-input destination is replaced only after successful completion;
- handled failure cleans temp output where possible.

### One-owner integration

- direct API and workflow adapter delegate to the same writer/capability owner;
- equivalent direct/workflow execution is byte-identical;
- adapter does not reimplement decoding/formatting/publication;
- shared platform file-URI interpretation is reused instead of copied into the Node Pack.

### M4 semantics

- `files.literal` justifies `PURE` and can be CACHED only while file Artifacts remain valid;
- `text.merge.files` remains `NEVER` because publication is required;
- output Artifact carries current run/node provenance;
- ArtifactRegistry records a strong executed occurrence.

### Hosted promotion

Required hosted evidence is Ubuntu/Windows × Python 3.10/3.13 plus the existing xyflow job. Root CI must also execute a real Text workflow smoke and assert exact generated content.

Accepted Text code candidate `dbd39a1119ce1557d802a115404f01a3f797d93e` passed run `33627879876`: representative Ubuntu/Python 3.10 executed 72 core + 64 JSON + 15 Text tests and all core/JSON/Text smokes successfully.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run. Until process/session ownership proves atomic acquisition, liveness/takeover and side-effect replay/idempotency: do not automatically continue old RUNNING work; do not emit RECOVERED; use a new run and validated completed PURE results; keep M2 INTERRUPTED reconciliation authoritative.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Automatic cleanup of temporary/intermediate files requires explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown custom objects. Shareable diagnostics additionally require redaction regression tests and must not snapshot the complete environment-variable set.

## External/native boundaries

If a capability crosses a real external boundary (FFmpeg, PowerShell, browser, auth, subprocess application, OS integration), unit mocks alone are insufficient. Use the lowest real boundary that proves the claim and record environment/version information where material.

## Failure classification

A CI failure counts as product evidence only after the job reaches the corresponding boundary.

Examples:

- runner/billing failure before steps: platform/harness boundary;
- editable install failure: packaging boundary;
- unit test failure: code/contract boundary;
- workflow/CLI failure after passing unit tests: integration/runtime boundary;
- PowerShell/FFmpeg subprocess failure: native dependency boundary;
- support-bundle assertion failure: diagnostics/forensics boundary.

Do not change product code to fix a failure that never reached product code.

## Carry-forward policy

Evidence from a previous SHA may only be reused when the relevant code, tests and runtime boundary are shown equivalent.

Each major milestone/slice records its exact candidate and hosted run IDs under `docs/specs/<milestone>/evidence.md` before being marked resolved. A code candidate may be accepted before memory closure, but promotion waits for synchronized canonical state/decision/journal/roadmap documentation and required exact-head hosted evidence.

# Testing / Evidence Policy — K-Tools Neo

## Evidence ladder

1. Static/syntax checks — structure only.
2. Unit tests — isolated model/capability rules.
3. Contract tests — node/port/journal/diagnostics/cache/artifact/adapter contracts.
4. CLI smoke — real headless workflow execution boundary.
5. Integration tests — real Node Packs/adapters/subsystems exercised together.
6. Native smoke — Windows/PowerShell/FFmpeg/browser/subprocess boundary where required.
7. E2E — production editor/tool → engine → capability → durable run/artifact/cache/result/diagnostic bundle.

Do not promote evidence across levels.

A green job proves only the commands that job actually reached and completed.

## Root hosted CI

`.github/workflows/core-ci.yml` validates two surfaces.

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
10. JSON workflow CLI smoke;
11. generated JSON-part verification;
12. Text workflow smoke;
13. exact generated Text artifact verification.

Because suites are discovered from the repository, the matrix exercises Durable Execution, Diagnostics/Support Bundle and M4 Artifact/Cache contracts together, including SQLite lifecycle, safe redaction, support reports, subprocess failure boundaries, semantic cache reuse/invalidation and persistent Artifact observations. M5 additionally exercises FILE_SET and the official Text Node Pack.

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

Minimum evidence includes:

- structured severity/kind/category/component fields;
- run/workflow/node correlation through real engine execution;
- decisions, metrics, batches and anomaly records;
- exception type/message/traceback capture;
- stdlib Python logging bridge;
- recursive credential-pattern redaction;
- command-argument redaction;
- unknown-object repr non-leakage;
- support-bundle creation containing `session.json`, `report.md`, `report.json`, `diagnostics.jsonl` and referenced raw logs;
- human report reconstruction of environment, executed steps, batches, decisions, metrics/quality observations, anomalies, subprocesses, errors, results and Run Journal lifecycle;
- real subprocess stdout/stderr + exit-code evidence;
- subprocess timeout and launch-failure evidence;
- PowerShell stdout/stderr smoke where PowerShell is present;
- Ctrl+C/KeyboardInterrupt classification as `INTERRUPTED`;
- stale incomplete-session recovery without classifying a fresh session as abandoned;
- a real official Node Pack success bundle and failure bundle;
- seeded fake secrets absent from shareable report/event/raw material;
- Windows/Linux hosted regression.

### Diagnostic evidence boundaries

A support bundle is forensic evidence, not proof of root cause. `diagnosticHotspots` may summarize recorded WARNING/ERROR/ANOMALY facts but must not be described as automatic causal diagnosis.

A missing final report is not sufficient proof of a crash while a process might still be alive. Abandoned-session recovery retains a staleness/ownership boundary until a stronger lease mechanism exists.

Low model accuracy or inconsistent domain results must be asserted by the domain capability/model adapter using explicit metric/anomaly records. Core diagnostics records the observation; it does not invent a universal quality threshold.

## Artifact Lifecycle + Semantic Cache V1 evidence expectations

A claim that a node result is safely reusable requires all applicable dimensions below; a previous successful run alone is insufficient.

### Artifact validity

For strong local-file reuse evidence:

- snapshot includes normalized file identity, size, mtime-ns, SHA-256 and observation time;
- unchanged file validates;
- missing file invalidates;
- size/mtime change invalidates quickly;
- same-size content mutation must still invalidate when mtime is restored;
- file change during hashing/validation must fail closed;
- unsupported directory/remote URI must not be mislabeled strongly valid;
- content identity must not depend on random Artifact/run ids.

### Semantic signature

Tests must prove that signature identity includes at least:

- node type;
- declared implementation version;
- canonical config;
- semantic input values;
- Artifact content identity when Artifact input semantics are content-based.

Equivalent JSON mapping order must not change the signature. Config/input/version/Artifact-content changes must change it. Opaque or nondeterministically serializable values must disable/bypass cache rather than guess.

### Persistent cache

A persistent cache claim requires:

- close/reopen persistence;
- origin run/node provenance;
- deterministic, collision-safe output serialization;
- Artifact output rehydration when supported;
- output Artifact strong revalidation before reuse;
- explicit invalidation/removal behavior;
- cache-store failure normalization;
- proof that cache failure does not become workflow failure when normal execution can proceed.

### Engine lifecycle truth

A real cache hit must prove the handler did not execute, preferably with call-count instrumentation.

Journal semantics for a reused node are:

```text
RUN_STARTED
NODE_CACHED
RUN_SUCCEEDED
```

A reused node must not emit fake `NODE_STARTED`; SQLite projection status is `CACHED`.

A `NEVER` node must always execute even if an apparently equivalent prior output exists.

### Artifact registry

Persistent Artifact lifecycle evidence requires occurrence records tied to:

- current run;
- current node;
- output port;
- nested value path where relevant;
- source `EXECUTED` or `CACHED`;
- original Artifact identity/provenance;
- strong snapshot or explicit unsupported/error state.

Historical snapshot evidence must remain queryable after current filesystem mutation.

### Real workload

Fixture nodes are insufficient for milestone promotion. At least one official product capability must prove meaningful reuse or must explicitly prove why its side-effect contract forbids reuse.

M4 acceptance includes both:

- `json.split.plan`: a real PURE transformation over the shared `split_json_document` owner, exercised with 2,000 records and cache close/reopen;
- `json.split`: a side-effectful `NEVER` node that republishes files on the second run even when its source is CACHED.

### Diagnostics

When diagnostics is active, cache decisions must leave concise operational facts such as:

- policy bypass;
- signature unsupported;
- lookup miss;
- validated hit;
- output Artifact invalidation reason;
- cache read/write/touch/invalidation failure.

Do not store private chain-of-thought. Record decision + concrete observed reason.

## Text Node Pack V1 evidence expectations

A claim that Markdown/TXT merge is migrated behind the platform requires all applicable layers below.

### FILE_SET contract

- explicit ordered `DataType.FILE_SET` exists;
- FILE_SET→FILE_SET validates while FILE and FILE_SET do not silently coerce;
- `files.literal` preserves configured order and emits FILE Artifacts;
- `files.literal` is PURE only because it has no publication side effect and M4 revalidates cached file outputs;
- changing a source file invalidates the cached source result and forces execution.

### Legacy behavior characterization

- `utf-8-sig`/UTF-8/latin-1 reading order is proved;
- `completo`, `simples` and `nenhum` exact bytes are proved;
- input ordering and output suffix normalization are proved;
- output/input collision is rejected;
- output parent creation is covered;
- existing destination replacement happens only after complete temp output;
- handled mid-operation failure preserves the previous destination and cleans temp output where possible.

### One-owner direct/workflow proof

- direct API and node adapter both delegate to the same writer;
- equivalent direct/workflow executions are byte-identical;
- adapter does not reimplement decoding/formatting/publication;
- shared platform `file://` interpretation is reused rather than copied into a pack.

### M4 integration

- `text.merge.files` is NEVER because publication/replacement is required;
- output is a first-class FILE Artifact with current run/node provenance;
- ArtifactRegistry records an EXECUTED occurrence with a strong snapshot;
- a cached upstream `files.literal` does not cause the merge publication node to be skipped.

### Hosted promotion

Root CI must install and test `ktools-text` on Ubuntu/Windows × Python 3.10/3.13 and execute a real Text workflow smoke with exact output assertion. The existing xyflow job must remain green.

Accepted code candidate `dbd39a1119ce1557d802a115404f01a3f797d93e` passed run `33627879876`. Representative Ubuntu/Python 3.10 evidence: 72 core tests + 64 JSON tests + 15 Text tests, all OK, followed by core CLI, JSON workflow/artifact and Text workflow/exact-content smokes.

## Recovery / ownership evidence boundary

M4 restart reuse is not equivalent to continuing an old in-flight run.

Until a process/session ownership contract proves atomic acquisition, liveness/takeover and side-effect replay/idempotency:

- do not automatically continue old `RUNNING` work;
- do not emit `RECOVERED`;
- use a new run and selectively reuse validated completed PURE results;
- keep M2 explicit `INTERRUPTED` reconciliation authoritative for abandoned old runs.

## Retention / deletion evidence boundary

Cache and Artifact-registry databases own metadata, not user output files.

Deleting/invalidation of cache metadata must not silently delete user Artifacts. Automatic cleanup of temporary/intermediate files requires a later explicit ownership contract proving which files K-Tools may delete safely.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown custom objects.

Diagnostics intended for sharing additionally require redaction regression tests. Do not snapshot the complete environment-variable set or store credentials merely for convenience.

This does not mean every conceivable sensitive string can be recognized automatically. Callers must still explicitly mark/avoid highly sensitive payloads and future adapters must review their own boundaries.

## External/native boundaries

If a capability crosses a real external boundary (FFmpeg, PowerShell, browser, auth, subprocess application, OS integration), unit mocks alone are insufficient for claims about that boundary.

Use the lowest real boundary that proves the claim and record environment/version information where material. Future subprocess-heavy capabilities use the common diagnostics boundary so failed native executions leave shareable evidence.

## Failure classification

A CI failure counts as product evidence only after the job reaches the corresponding boundary.

Examples:

- runner/billing failure before steps: platform/harness boundary;
- editable install failure: packaging boundary;
- unit test failure: code/contract boundary;
- CLI failure after passing unit tests: integration/runtime boundary;
- PowerShell/FFmpeg subprocess failure: native dependency boundary;
- support-bundle assertion failure: diagnostics/forensics boundary.

Do not change product code to fix a failure that never reached product code.

## Carry-forward policy

Evidence from a previous SHA may only be reused when the relevant code, tests and runtime boundary are shown to be equivalent.

Each major milestone records its exact candidate/head and hosted run IDs under its own `docs/specs/<milestone>/evidence.md` before being marked resolved. A code candidate may be accepted before memory closure, but the milestone is not promoted until canonical state/decision/journal/roadmap documentation is synchronized and the required exact promotion head passes hosted evidence.

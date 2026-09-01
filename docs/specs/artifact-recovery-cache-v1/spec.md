# Spec — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **IMPLEMENTATION COMPLETE / FINAL MEMORY-HEAD CI PENDING**
Milestone: M4
Owner/implementer: ChatGPT Solo Development Mode

## Problem

M2 can tell which nodes ran and M3 can reconstruct why a run behaved as recorded, but K-Tools also needs to answer conservatively:

- is an output Artifact from an older run still present and unchanged?
- can a node result be reused instead of recomputed?
- did config/input/node implementation change since the cached result?
- is a node safe to skip at all, or does it own required side effects?
- why was a cache candidate reused or rejected?

Blindly reusing a previous successful node output is unsafe. Files may be deleted/modified externally, node code may change, config may change, and some nodes must execute because they publish side effects.

## Goal

Create a conservative local-first Artifact lifecycle and semantic-cache foundation that proves reuse without returning stale/missing output and without skipping side-effectful nodes accidentally.

## V1 architectural rules

### Cacheability is explicit opt-in

Node definitions carry a version and cache policy.

V1 policies:

- `NEVER` — default; always execute;
- `PURE` — deterministic output for equivalent semantic inputs/config and no externally required side effect.

Additional policies may appear only with evidence. Do not infer purity from implementation shape.

`json.split` remains `NEVER` because its required behavior includes file publication/collision policy. `json.split.plan` exposes the same real transformation owner without I/O and is `PURE`.

### Strong local-file validity

For `file://` Artifacts, V1 records:

- normalized local path/URI;
- file size;
- mtime-ns as quick-change evidence;
- SHA-256 content digest as strong identity;
- observation timestamp.

On reuse:

1. missing file → invalid;
2. size/mtime mismatch → invalid quickly;
3. if quick fields still match, recompute SHA-256 before claiming strong validity.

Directories and remote URIs are not strongly cache-valid in V1. Unsupported cases remain observable but cannot be promoted to a strong-validity claim.

### Stable semantic node signature

Canonical signature input includes:

- node type id;
- declared node implementation/version;
- canonicalized config;
- semantic input values;
- Artifact inputs represented by stable content identity instead of random Artifact/run ids;
- explicit signature extras when required by later capabilities.

Canonical JSON is sorted and hashed with SHA-256. Unknown/non-deterministically serializable values disable caching instead of guessing. Mapping keys must be strings to avoid canonicalization collisions.

### Persistent cache records

`SQLiteNodeCache` persists:

- cache signature;
- node type/version;
- originating run/node;
- safely encoded outputs;
- output Artifact snapshots;
- creation/last-used timestamps.

The cache is an optional injected optimization. Cache read/write/touch/invalidation failures do not turn a valid workflow into a failed workflow.

### Persistent Artifact lifecycle observations

`SQLiteArtifactRegistry` records Artifact occurrences independently from the semantic cache and binds them to:

- current run id;
- current node id;
- output port;
- nested value path;
- source (`EXECUTED` or `CACHED`);
- original Artifact id/provenance/metadata;
- strong snapshot when supported;
- explicit snapshot error when strong validity is unsupported.

The registry never deletes or mutates user files.

### Reuse must revalidate outputs

A matching signature is necessary but not sufficient when cached outputs reference files. Every cached file Artifact must pass strong current validity before reuse. Missing/modified outputs invalidate the candidate and the node executes normally.

### Diagnostics explains cache decisions

With Diagnostics active, cache decisions record concise observed reasons including policy bypass, lookup error/miss, write outcome, validation failure and validated reuse. Cache and Artifact registry failures are supplemental evidence, not a reason to corrupt successful business execution.

## Lifecycle semantics

M4 adds explicit `NODE_CACHED` / `NodeRunStatus.CACHED` only when the handler was genuinely skipped. A cached node does not emit `NODE_STARTED` or pretend to be ordinary execution success.

`RECOVERED` is deliberately not emitted in V1.

## Recovery / ownership

Accepted boundary: `ownership-recovery-boundary.md`.

M4 recovery means **start a new run and selectively reuse strongly validated completed PURE results**. It does not mean continuing an old in-flight run.

Automatic resume/reclaim of old `RUNNING` work remains unavailable until a future ownership/lease contract proves atomic ownership, liveness/takeover and side-effect replay safety.

## Acceptance slices

### Slice A — Artifact snapshot / validity

- [x] file Artifact can be snapshotted with SHA-256;
- [x] unchanged file validates;
- [x] deleted file invalidates;
- [x] same-size modification with restored mtime still invalidates through digest;
- [x] unsupported URI/type fails closed for strong validity;
- [x] content identity contains no random run/artifact id.

### Slice B — cache policy + signature

- [x] NodeDefinition default policy is NEVER;
- [x] PURE nodes can be signed;
- [x] signature is independent of random run/artifact ids;
- [x] config change changes signature;
- [x] node version change changes signature;
- [x] scalar/JSON input change changes signature;
- [x] Artifact content change changes signature;
- [x] unsupported/opaque input disables caching safely;
- [x] mapping-key collision risks fail closed.

### Slice C — persistent cache + engine reuse

- [x] cache entry survives SQLite close/reopen;
- [x] PURE node second equivalent execution is served from validated cache;
- [x] handler call count proves cached node was not executed;
- [x] modified/missing output forces execution;
- [x] NEVER node always executes;
- [x] `NODE_CACHED` / `CACHED` semantics are explicit;
- [x] diagnostics records hit/miss/bypass/invalidation reasons;
- [x] cache failures fail open;
- [x] cache output codec cannot collide with user JSON markers;
- [x] existing no-cache engine API remains compatible;
- [x] CLI `--cache` proves persistence across separate invocations.

### Slice D — real workload

- [x] official `json.literal` is explicitly PURE;
- [x] side-effectful `json.split` remains NEVER and republishes files on repeated execution;
- [x] new official `json.split.plan` delegates to the real pure `split_json_document` owner;
- [x] a 2,000-record split-plan workload is reused after cache close/reopen;
- [x] patched owner call count proves `split_json_document` ran once across two equivalent runs;
- [x] second run projects source/planner as CACHED where appropriate.

### Slice E — persistent Artifact provenance

- [x] Artifact occurrence survives registry close/reopen;
- [x] run/node/output-port/value-path provenance persists;
- [x] current validity can be rechecked without erasing the historical snapshot;
- [x] unsupported strong-validity cases remain explicit rather than guessed;
- [x] runtime records EXECUTED and CACHED occurrences separately;
- [x] registry failure is supplemental/fail-open;
- [x] both first-party CLIs expose `--artifact-registry`.

### Slice F — recovery/retention safety

- [x] restart reuse is defined as a new run using validated completed cache entries;
- [x] old RUNNING rows are not auto-resumed/reclaimed;
- [x] RECOVERED remains ownership-gated;
- [x] ownership requirements are documented before future automatic resume;
- [x] V1 never deletes user Artifact files automatically;
- [x] cache/registry databases are metadata stores that may be discarded without altering user outputs.

## Non-goals / explicit V1 boundaries

- distributed/shared cache;
- remote object-store validation;
- implicit cacheability inference;
- cache of arbitrary opaque Python objects;
- broad automatic resume of interrupted processes;
- `RECOVERED` semantics without executable ownership evidence;
- skipping side-effectful nodes without replay/publication semantics;
- automatic deletion of user output files;
- performance shortcuts that can knowingly return stale file content.

## Required regression

- [x] M0-M3 tests and CLI smokes remain green on accepted code candidate;
- [x] support bundles describe cache decisions;
- [x] real JSON publication semantics remain intact;
- [x] hosted Ubuntu/Windows Python 3.10/3.13 + xyflow passed on accepted code candidate;
- [ ] final canonical documentation/memory HEAD passes the same hosted matrix before M5 code starts.

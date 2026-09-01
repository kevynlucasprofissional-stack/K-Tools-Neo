# Spec — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **ACTIVE**
Milestone: M4
Owner/implementer: ChatGPT Solo Development Mode

## Problem

M2 can tell which nodes ran and M3 can reconstruct why a run behaved as recorded, but K-Tools still cannot safely answer:

- is an output artifact from an older run still present and unchanged?
- can a node result be reused instead of recomputed?
- did config/input/node implementation change since the cached result?
- is a node safe to skip at all, or does it own required side effects?
- why was a cache candidate reused or rejected?

Blindly reusing a previous successful node output is unsafe. Files may be deleted/modified externally, node code may change, config may change, and some nodes must execute because they publish side effects.

## Goal

Create a conservative local-first Artifact lifecycle and semantic-cache foundation that can prove cache reuse without returning stale/missing output and without skipping side-effectful nodes accidentally.

## V1 architectural rules

### Cacheability is explicit opt-in

Node definitions gain a version and cache policy.

V1 policies:

- `NEVER` — default; always execute;
- `PURE` — deterministic output for equivalent semantic inputs/config and no externally required side effect.

Additional policies may appear only with evidence. Do not infer purity from implementation shape.

`json.split` remains `NEVER` initially because its required behavior includes file publication/collision policy. Skipping execution would require a proved replay/publication contract, not merely cached metadata.

### Strong local-file validity

For `file://` Artifacts, V1 records a snapshot including:

- normalized local path/URI;
- file size;
- mtime-ns as quick-change evidence;
- SHA-256 content digest as strong identity;
- observation timestamp.

On reuse:

1. missing file → invalid;
2. size/mtime mismatch → invalid quickly;
3. if quick fields still match, recompute SHA-256 before claiming strong validity.

This deliberately favors correctness over maximum hashing speed. Later performance work may add trusted filesystem identity/content-addressed storage, but may not silently weaken correctness.

Directories and remote URIs are not strongly cache-valid in first V1 unless a dedicated policy is added with tests.

### Stable semantic node signature

A cache key must not depend on random run IDs/artifact IDs.

Canonical signature input includes at least:

- node type id;
- declared node implementation/version;
- canonicalized config;
- semantic input values;
- for Artifact inputs: stable type + content validity identity rather than random Artifact id;
- relevant explicit signature extras when a capability's semantics depend on path/name or other external identity.

Canonical JSON is sorted and hashed with SHA-256.

Unknown/non-deterministically serializable input prevents caching instead of guessing.

### Persistent cache records

V1 persists cache entries locally (stdlib SQLite preferred) with:

- cache key/signature;
- node type/version;
- originating run/node;
- output metadata;
- output Artifact snapshots where applicable;
- created/last-used timestamps;
- validity/invalidation observations when useful.

Cache persistence is a separate concern from Run Journal but uses run/node identity for provenance.

### Reuse must revalidate outputs

A matching signature is necessary but not sufficient when cached outputs reference files.

All referenced cache-owned/reusable file Artifacts must pass strong validity before reuse.

A missing/modified output invalidates the candidate and the node executes normally.

### Diagnostics explains cache decisions

When Diagnostics is active, every cache decision emits concise operational evidence such as:

- cache disabled by policy;
- cache lookup miss;
- signature match;
- file missing;
- size/mtime changed;
- content digest mismatch;
- candidate valid → reused;
- candidate invalid → recomputed.

Do not expose private chain-of-thought. Record decision + concrete observed reason.

## Lifecycle semantics

M4 may introduce `CACHED` only when a node is genuinely not executed and its validated prior output is substituted.

Do not overload `SUCCEEDED` to hide cache reuse if the UI/history needs to distinguish them.

`RECOVERED` remains gated until a real restart/recovery path can prove that semantics separately from ordinary cache lookup.

## Recovery / ownership

M4 must investigate a process/session ownership model before automatic resume of previously RUNNING work.

A stale/incomplete run is evidence for investigation, not enough to assume exclusive recovery ownership.

V1 may deliver safe cache reuse before full interrupted-node resume if ownership evidence is not yet sufficient.

## First acceptance slices

### Slice A — artifact snapshot / validity

- [ ] file Artifact can be snapshotted with SHA-256;
- [ ] unchanged file validates;
- [ ] deleted file invalidates;
- [ ] content modification invalidates even if size is preserved;
- [ ] attempt to strong-validate unsupported URI/type fails closed;
- [ ] snapshots contain no random run-specific field in content identity.

### Slice B — cache-policy + signature

- [ ] NodeDefinition default policy is NEVER;
- [ ] opt-in PURE built-in fixture node can be signed;
- [ ] signature stable across process/run IDs;
- [ ] config change changes signature;
- [ ] node version change changes signature;
- [ ] scalar/JSON input change changes signature;
- [ ] Artifact content change changes signature;
- [ ] unsupported nondeterministic input disables/fails cache lookup safely.

### Slice C — persistent cache + engine reuse

- [ ] cache entry survives SQLite close/reopen;
- [ ] PURE node second equivalent execution can be served from validated cache;
- [ ] handler call count proves cached node was not executed;
- [ ] modified/missing output forces execution;
- [ ] NEVER node always executes;
- [ ] cached status/event semantics are explicit;
- [ ] diagnostics records hit/miss/invalidation reason;
- [ ] existing no-cache/no-store engine API remains compatible.

### Slice D — real workload

A real product capability must eventually prove reuse or explain why its current side-effect contract prevents caching.

Prefer adding a genuinely cache-safe local transformation before weakening `json.split` publication semantics merely to satisfy the test.

## Non-goals

- distributed/shared cache;
- remote object-store validation;
- implicit cacheability inference;
- cache of arbitrary opaque Python objects;
- broad automatic resume of interrupted processes;
- skipping side-effectful nodes without replay/publication semantics;
- performance shortcuts that can knowingly return stale file content.

## Required regression

- M0-M3 tests and CLI smokes remain green;
- support bundles continue to describe cache decisions when diagnostics is active;
- hosted Windows/Linux CI remains required for promotion.

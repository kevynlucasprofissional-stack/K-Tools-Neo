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

### Python runtime + official JSON/Text/PDF/Documents/Images Node Packs

Matrix:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13.

Each matrix job performs checkout/Python setup; editable install of Core, JSON, Text, PDF, Documents and Images in dependency order; the complete suite for every installed pack; Core CLI smoke; JSON split smoke; Text merge and split→merge smokes; PDF merge and split→merge smokes; Documents mixed Text/PDF smoke; and a generated lossless RGB/RGBA WebP→PNG workflow smoke that reopens emitted PNGs and verifies exact mode/size/pixels.

`ktools-images` must obtain Pillow from its package metadata, not an execution-time installer. Current V1 dependency is `Pillow>=12,<13`.

Because suites are discovered from the repository, the matrix also exercises Durable Execution, Diagnostics/Support Bundle and M4 Artifact/Cache contracts together, including SQLite lifecycle, safe redaction, support reports, subprocess failure boundaries, semantic cache reuse/invalidation and persistent Artifact observations.

### xyflow spike

Ubuntu / Node.js 22 performs checkout, Node setup, `npm ci`, build, lint and deterministic Vitest tests. This protects the audited spike from silent regression; it does not promote the spike into the production editor.

## Durable Execution V1 evidence expectations

A durable-execution claim requires success lifecycle ordering; handler/output-contract failure lifecycle; no-journal compatibility; SQLite write/close/reopen/query; persisted run/node terminal state; JSON-safe output metadata; explicit incomplete `RUNNING -> INTERRUPTED` reconciliation; real official Node Pack execution; and Windows/Linux hosted regression. Cache and automatic resume are separate claims.

## Diagnostics + Support Bundle V1 evidence expectations

Minimum evidence includes structured severity/kind/category/component fields; run/workflow/node correlation; decisions, metrics, batches and anomalies; exception traceback; stdlib logging bridge; recursive redaction; command redaction; unknown-object non-leakage; support bundle creation; human report reconstruction; real subprocess stdout/stderr/exit code; timeout and launch-failure evidence; PowerShell where available; Ctrl+C classification; stale-session recovery; real Node Pack success/failure bundles; seeded secret non-leakage; and Windows/Linux hosted regression.

A support bundle is forensic evidence, not proof of root cause.

## Artifact Lifecycle + Semantic Cache V1 evidence expectations

Reusable node results require explicit PURE policy, deterministic semantic signature and valid outputs. Strong local-file snapshots include normalized identity, size, mtime-ns, SHA-256 and observation time. Persistent cache evidence requires close/reopen persistence, provenance, Artifact rehydration/revalidation, explicit invalidation, failure normalization and fail-open execution. A hit must prove the handler did not execute. Reused lifecycle is `RUN_STARTED -> NODE_CACHED -> RUN_SUCCEEDED`; NEVER nodes always execute.

ArtifactRegistry evidence binds occurrences to current run/node/output port/value path, EXECUTED/CACHED source, original Artifact provenance and strong snapshot or explicit unsupported/error state.

## Text Merge Node Pack V1 evidence expectations

Requires ordered FILE_SET, exact compatibility, characterized decode/separator bytes, order/suffix/collision/temp-publication behavior, prior destination preservation on handled failure, direct/node shared owner and byte equivalence, centralized local URI parsing, `text.merge.files` NEVER, ArtifactRegistry proof, cached source without skipped publication and hosted exact-output smoke.

Final closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` / `33631040505`.

## PDF Merge Node Pack V1 evidence expectations

Requires explicit pypdf dependency, non-empty ordered inputs, fail-closed protected/corrupt/zero-page handling, deterministic page order, suffix normalization, input/output collision rejection, same-directory temp publication, prior destination preservation, semantic reopen equivalence, `pdf.merge.files: FILE_SET -> PDF` v1 NEVER, one writer owner, PDF Artifact provenance/strong snapshot, cached source without skipped publication and hosted reopen smoke.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` / `33651923578`, 5/5.

## PDF Split Node V1 evidence expectations

Requires `file.literal`, honest FILE/FILE_SET cardinality, integer parts >=2, clamp/balanced contiguous ranges, collision-safe names, fail-closed protected/corrupt/empty input, progress, per-part atomic publication, explicit later-part failure semantics, `pdf.split.parts: FILE -> FILE_SET` v1 NEVER, PDF Artifact page metadata/provenance, nested snapshots, one splitter owner, cached source without skipped publication, repeated re-publication, direct/workflow equivalence and hosted split→merge proof.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870`, 5/5.

## Text Split Node V1 evidence expectations

Requires split-specific `.md/.txt` decode characterization, integer parts >=2, line-unit preservation/clamp/balancing, UTF-8 collision-safe per-output publication, explicit later-part failure semantics, `text.split.parts: FILE -> FILE_SET` v1 NEVER, FILE Artifact metadata/snapshots, one splitter owner, cached source without skipped publication, direct/workflow byte equivalence and hosted split→merge proof.

Terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

## Mixed Document Split Orchestrator V1 evidence expectations

A mixed `.md/.txt/.pdf` claim requires supported-input filtering, source order, integer `parts>=2`, Text/PDF dispatch to canonical owners, equal source progress spans, per-source error accumulation/continuation, source→part output flattening, partial success as successful node+report, zero-success failure, structured report counts/errors/destination, no primitive Text/PDF algorithm in Documents, `document.split.files: FILE_SET -> FILE_SET + JSON` v1 NEVER, exact child Artifact preservation, current provenance/snapshots, cached-upstream/republication proof and explicit inherited child transaction boundaries.

Evidence: spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`; RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`; GREEN `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`; terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.

## Image Safety Foundation + WebP→PNG V1 evidence expectations

A WebP→PNG migration claim requires all of the following.

### Dependency / safety

- `Pillow>=12,<13` declared in `ktools-images` package metadata;
- 80,000,000-pixel ceiling plus Pillow bomb warning/error handling;
- positive dimensions and pixel count validated around orientation normalization;
- no execution-time self-installer inside the capability.

### Image semantics

- only existing `.webp` regular files are compatible inputs; empty compatible set fails closed;
- source order is preserved;
- EXIF orientation is normalized before final publication;
- animated WebP intentionally uses frame 0 only and exposes this policy in metadata/progress evidence;
- RGBA/LA/transparent palette sources preserve alpha in RGBA PNG;
- RGB/L remain valid modes; other non-alpha modes normalize to RGB;
- generated PNGs are reopened for real pixel/mode/size verification.

### Publication / failure

- output folder is explicit;
- names are case-insensitive collision-safe `{stem}.png`, `_1`, ...;
- each PNG uses same-directory temp→replace publication;
- current failing source leaves no partial final/temp output;
- a later source failure may leave earlier successfully published PNGs; batch rollback is not inferred;
- node is `CachePolicy.NEVER`, so a cached `files.literal` source still produces a fresh collision-safe publication.

### Architecture / Artifact

- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1;
- members are IMAGE Artifacts with `image/png` MIME and current run/node provenance;
- metadata records source/frame/orientation/mode/dimensions;
- ArtifactRegistry strongly snapshots nested outputs;
- direct API and workflow node delegate to one converter owner;
- API/node do not contain Pillow decode/EXIF/save/bomb/temp-publication algorithms;
- no `IMAGE_SET` is introduced without graph-time evidence.

### Hosted evidence

- spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / `33666227293`, 5/5;
- RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304`: observed Ubuntu 3.13 lane passed 76 Core + 64 JSON + 28 Text + 24 PDF + 7 Documents, installed Pillow 12.3.0, then failed exactly because `ktools_images` was absent;
- GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076`, 5/5;
- every Python lane installed Images, passed the Image suite and passed real generated RGB/RGBA WebP→PNG workflow smoke;
- xyflow remained green.

Formal promotion additionally requires the synchronized Slice-6 memory-closure HEAD to pass the same five hosted jobs.

## Recovery / ownership evidence boundary

M4 restart reuse is not continuation of an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative.

## Retention / deletion evidence boundary

Cache/Artifact-registry stores own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Cleanup of published/intermediate files requires explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

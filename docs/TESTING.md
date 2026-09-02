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

Each matrix job performs checkout/Python setup; editable install of Core, JSON, Text, PDF, Documents and Images in dependency order; the complete suite for every installed pack; Core CLI smoke; JSON split smoke; Text merge and split→merge smokes; PDF merge and split→merge smokes; Documents mixed Text/PDF smoke; generated lossless RGB/RGBA WebP→PNG workflow smoke that reopens emitted PNGs and verifies exact mode/size/pixels; and Images→PDF workflow smoke that creates deterministic image sources, executes `files.literal -> image.files_to_pdf`, reopens the PDF through `pypdf`, and verifies page count/order plus PDF Artifact semantics.

`ktools-images` must obtain Pillow from its package metadata, not an execution-time installer. Current V1 dependency is `Pillow>=12,<13`. `pypdf` is already installed through `ktools-pdf` in the root matrix and is an independent Images→PDF smoke/test oracle, not an Images→PDF runtime dependency.

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

A WebP→PNG migration claim requires `Pillow>=12,<13`; 80M-pixel/decompression-bomb protection; positive dimensions; existing `.webp` filtering; preserved input order; EXIF normalization; intentional frame 0; alpha-preserving PNG behavior; collision-safe per-output same-directory temp→replace; explicit non-transactional batch failure; `image.webp_to_png: FILE_SET -> FILE_SET` v1 NEVER; IMAGE Artifact metadata/provenance/snapshots; cached source without suppressed publication; direct/node one-owner architecture; and hosted generated RGB/RGBA pixel/mode/size verification.

Evidence: spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / `33666227293`; RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304`; GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076`; terminal closure `9b9fc57bd4bfb28d7e23637651a30182ce6f8828` / `33668942264`, 5/5.

## Images→PDF Node V1 evidence expectations

An Images→PDF promotion claim requires all of the following.

### Shared reader / safety

- WebP→PNG and Images→PDF both consume one pack-local guarded first-frame reader;
- the reader owns Pillow bomb configuration/classification, original/post-orientation size validation, frame-0 selection, EXIF normalization and detached loaded image output;
- `Image.open`, bomb-warning setup and EXIF transpose are not duplicated across the two capability owners;
- the existing `Pillow>=12,<13` and 80M-pixel policy remains unchanged unless separately evidenced.

### Input / page semantics

- only existing regular JPG/JPEG/PNG/WebP/BMP/TIF/TIFF inputs are compatible, case-insensitively;
- missing/unsupported paths are filtered and compatible order is preserved;
- no compatible source fails closed;
- one input contributes exactly one first-frame page;
- EXIF normalization occurs before PDF page preparation;
- every PDF page is RGB;
- RGBA/LA/palette transparency is composited over pure white;
- page order and normalized page sizes are verified semantically after reopen.

### Aggregate publication / failure

- destination suffix normalizes to `.pdf`;
- all pages are prepared before aggregate serialization;
- one same-directory temp PDF is written and verified non-empty before replace;
- a pre-existing destination is replaced only after success;
- a corrupt later compatible source or forced serializer failure preserves the previous destination;
- temp output and prepared page objects are cleaned/closed best-effort on handled failure;
- unlike WebP→PNG, the capability has one singular aggregate transaction boundary and does not expose partial success.

### Node / Artifact / cache

- `image.files_to_pdf: FILE_SET -> PDF`, version 1, `CachePolicy.NEVER`;
- input FILE_SET members may be local FILE/IMAGE Artifacts; suffix/existence filtering remains capability-owned;
- output is one `DataType.PDF` Artifact with `application/pdf`, current provenance and ordered source/page/policy metadata;
- ArtifactRegistry records a strong local-file snapshot;
- a cached PURE `files.literal` does not suppress second Images→PDF execution/publication;
- direct API and workflow share one Images→PDF writer owner;
- API/node contain no Pillow decode/EXIF/RGB/composite/PDF-save/temp-publication algorithms;
- no `IMAGE_SET` is introduced without graph-time evidence.

### Hosted evidence

- spec `ae617e948d5549e3dbca1dbe8d5de19c16555535` / `33670517542`, 5/5;
- discriminating RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db` / `33671061268`, with prior suites and 15 old WebP tests green while 15 new Images→PDF contracts failed on the missing reader/PDF boundary;
- GREEN `309863ac475330448e6fc44dbdf305482528689e` / `33671740134`, 5/5;
- architecture hardening `1d9afc40bb7adbb511a1869d25b18058782bcbad` / `33672387118`, 5/5;
- every Python lane passed both image capability suites and both image hosted smokes; xyflow remained green.

Formal promotion additionally requires the synchronized Slice-7 memory-closure HEAD to pass the same five hosted jobs.

## Recovery / ownership evidence boundary

M4 restart reuse is not continuation of an old in-flight run. Until atomic ownership/liveness/takeover/side-effect replay is proved, start a new run and selectively reuse validated completed PURE results. M2 INTERRUPTED reconciliation remains authoritative.

## Retention / deletion evidence boundary

Cache/Artifact-registry stores own metadata, not user output files. Metadata invalidation must not silently delete user Artifacts. Cleanup of published/intermediate files requires explicit ownership evidence.

## Serialization / privacy safety evidence

Durable metadata and support diagnostics must not use arbitrary `repr()` or broad reflection of unknown objects. Shareable diagnostics require redaction regression tests. Do not snapshot complete environment-variable sets or store credentials for convenience.

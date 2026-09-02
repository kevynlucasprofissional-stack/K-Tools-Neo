# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

## Product destination

K-Tools Neo becomes one integrated local-first product where every reusable operation is a capability/node, simple Tools and visual Workflows share implementation owners, expensive/local work is observable/durable/diagnosable/conservatively reusable, official Node Packs cover local capability families, imported applications are adapted rather than rewritten, the UI is a client of stable runtime contracts, and later AI agents compose through the same catalog.

---

## M0 — Platform Foundation
Status: **RESOLVED / PROMOTED**

## M1 — First real Node Pack
Status: **RESOLVED** — `packages/ktools-json/`.

## M2 — Durable Execution V1
Status: **RESOLVED** — optional RunJournal + Memory/SQLite lifecycle history.

## M3 — Diagnostics, Structured Logging + Support Bundle
Status: **RESOLVED / PROMOTED** — structured/share-safe diagnostics, support bundles and native/subprocess evidence boundaries.

Final closure run: `33557338124` on `5e1e46714aaefe0827c96a415d7d58d57790a187`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1
Status: **RESOLVED / PROMOTED** — strong Artifact validity/provenance, explicit PURE/NEVER policy, persistent fail-open cache, CACHED lifecycle and conservative restart reuse.

Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

---

## M5 — Official local Node Packs

Status: **ACTIVE / ITERATIVE DELIVERY**

Capability families:

- Files/Folders;
- Text;
- Documents/Images/PDF;
- Media.

Slice rule: inspect the actual legacy owner before extraction; characterize behavior first; prefer bounded capabilities with explicit dependency/native/security risk; preserve one-owner direct API + workflow architecture; use first-class Artifacts; classify PURE versus required publication explicitly; integrate diagnostics at real native/subprocess boundaries; keep orchestration separate from primitive transformation ownership; establish third-party safety/version policy before broad capability families depend on it.

### Slice 1 — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered ordered FILE_SET, PURE `files.literal`, canonical `packages/ktools-text/`, characterized Markdown/TXT merge, `text.merge.files` NEVER, direct/workflow equivalence, ArtifactRegistry proof, centralized local URI parsing and hosted Text smoke.

Promotion `958d5bf563cda21673d69865d1508831c599c006` / `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` / `33631040505`.

### Slice 2 — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered `packages/ktools-pdf/`, `pypdf>=5,<7`, checked reading, ordered page merge, atomic publication, direct API, `pdf.merge.files: FILE_SET -> PDF` v1 NEVER, PDF Artifact provenance/snapshots, cache/publication proof and fail-closed protected/encrypted behavior.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` / `33651923578`, 5/5.

### Slice 3 — PDF Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered `file.literal`, canonical balanced PDF split, `pdf.split.parts: FILE -> FILE_SET` v1 NEVER, contiguous balanced planning, collision-safe per-part atomic publication, explicit partial-set failure, PDF Artifact metadata/snapshots, cache/republication proof and hosted split→merge composition.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870`, 5/5.

### Slice 4 — Text Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered split-specific decode policy, balanced line-unit planning, canonical split owner, UTF-8 collision-safe per-output publication, `text.split.parts: FILE -> FILE_SET` v1 NEVER, Artifact metadata/snapshots, cached-source/republication proof, direct/workflow equivalence and hosted split→merge composition.

Evidence: spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`; RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`; GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`; hardened `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`; terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

### Slice 5 — Mixed Document Split Orchestrator V1

Status: **RESOLVED / PROMOTED**

Delivered `packages/ktools-documents` as orchestration-only owner for `.md/.txt/.pdf`: ordered dispatch to canonical Text/PDF splitters, weighted progress, per-source continuation, partial-success JSON report, zero-success failure, child Artifact preservation, current provenance/snapshots, `document.split.files: FILE_SET -> FILE_SET + JSON` v1 NEVER, cache/republication proof and hosted mixed workflow smoke.

Evidence: spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`; RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`; GREEN `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`; terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.

Canonical batch owner: `packages/ktools-documents`; primitive owners remain `ktools-text`/`ktools-pdf`.

### Slice 6 — Image Safety Foundation + WebP→PNG V1

Status: **RESOLVED / PROMOTED**

Fresh discovery selected WebP→PNG over Images→PDF and Files/Folders because it established the reusable image-safety foundation with the smallest bounded semantic surface.

Delivered canonical `packages/ktools-images`, `Pillow>=12,<13`, 80M-pixel/decompression-bomb policy, EXIF normalization, frame-0 behavior, alpha-preserving PNG normalization, collision-safe per-output temp→promote publication, `image.webp_to_png: FILE_SET -> FILE_SET` v1 NEVER, IMAGE Artifacts, strong snapshots/cache-republication proof and real RGB/RGBA hosted smoke.

Evidence: spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / `33666227293`; RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304`; GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076`; terminal closure `9b9fc57bd4bfb28d7e23637651a30182ce6f8828` / `33668942264`, 5/5.

ADR: `docs/decisions/ADR-028-IMAGE-SAFETY-WEBP-PNG-V1.md`.
Canonical owner: `packages/ktools-images`. Stable-GUI WebP→PNG is compatibility debt.

### Slice 7 — Shared Image Reader + Images→PDF V1

Status: **RESOLVED / PROMOTED**

Fresh terminal-main discovery compared Images→PDF with bounded Files/Folders. Images→PDF won because the Slice-6 safety foundation reduced the remaining surface to a bounded aggregate-image/PDF contract, while Files/Folders still had overlapping legacy traversal/report owners with unresolved cross-platform semantics.

Delivered:

- `ktools_images.reader` as the one guarded Pillow decode / bomb / first-frame / EXIF owner shared by WebP→PNG and Images→PDF;
- WebP→PNG refactor with no observed behavior regression;
- existing JPG/JPEG/PNG/WebP/BMP/TIF/TIFF filtering in compatible-source order;
- one normalized first frame per source;
- RGB pages and alpha/palette transparency composited over white;
- one singular aggregate PDF, same-directory temp-written and promoted only after successful serialization;
- previous destination preservation on handled failure;
- canonical Images→PDF writer shared by direct API and node;
- `image.files_to_pdf: FILE_SET -> PDF`, v1 NEVER;
- one PDF Artifact with ordered metadata/provenance and strong snapshot;
- cached source without skipped publication;
- hosted `files.literal -> image.files_to_pdf` smoke independently reopened with `pypdf`;
- ownership-test hardening proving decode policy resides in the shared reader.

Evidence:

- spec `ae617e948d5549e3dbca1dbe8d5de19c16555535` / `33670517542`, 5/5;
- RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db` / `33671061268`;
- GREEN `309863ac475330448e6fc44dbdf305482528689e` / `33671740134`, 5/5;
- audited hardening `1d9afc40bb7adbb511a1869d25b18058782bcbad` / `33672387118`, 5/5;
- synchronized terminal memory closure `c3585f5b7f478f53e1c5ef63f72a7b49fbb0cdea` / `33674308145`, 5/5.

ADR: `docs/decisions/ADR-029-IMAGES-TO-PDF-NODE-V1.md`.
Canonical owner remains `packages/ktools-images`; stable-GUI Images→PDF is compatibility debt.

### Slice 8 — FRESH DISCOVERY GATE

Status: **ACTIVE / NO CANDIDATE SELECTED YET**

Inspect exact terminal `main` and compare at minimum:

- bounded Files/Folders operations;
- the smallest useful Media capability;
- any remaining image/document utility only if it offers a clearer contract and stronger product/composition value.

Files/Folders must lock root validity, files/dirs inclusion, hidden handling, recursion, symlink/reparse behavior, deterministic ordering, permission/OSError aggregation, progress/report schema and observation/publication ownership before coding.

Media must establish a shared FFmpeg/FFprobe process boundary using M3 diagnostics and explicit M4 Artifact/cache semantics before broad audio/video nodes are promoted.

Do not infer the Slice-8 winner from previous preference. Run fresh discovery against the exact terminal Slice-7 mainline.

---

## M6 — Imported application adapters
Status: **PLANNED** — expose YT-DLP TUI and XCursos through explicit adapters while preserving mature internals.

## M7 — Runtime Contract API for UI
Status: **PLANNED** — machine-readable Node Pack/catalog/config/workflow/validation/run/artifact/diagnostic contracts.

## M8 — Production Workflow Editor
Status: **PLANNED** — production xyflow editor consumes runtime truth; frontend does not become engine.

## M9 — Ready-made Tools + Templates
Status: **PLANNED** — project workflows as simple Tools without duplicate logic.

## M10 — Desktop Product / Packaging
Status: **PLANNED / DECISION GATED** — choose Windows-first host after runtime/UI contracts stabilize.

## M11 — Agent-first composition
Status: **LATER** — natural language composes/repairs workflows through the same catalog/runtime.

## M12 — Release hardening
Status: **CONTINUOUS + FINAL RELEASE GATE** — CI, licenses, duplicate-owner removal, profiling, diagnostics, versioning, security and clean-Windows installer smoke.

---

## Execution rule

Take the first unresolved milestone/slice whose prerequisites are satisfied and work through explicit discovery -> spec -> evidence -> RED -> GREEN -> REFACTOR/AUDIT -> regression -> hosted evidence -> memory closure.

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in DoD. Every cacheable capability justifies purity, semantic identity and output validity explicitly. Every file cardinality remains honest. Every multi-output capability states its transaction boundary. Orchestration layers preserve child owners. Third-party decoding/execution boundaries receive explicit version/safety policy before broad reuse. Shared policy extraction requires at least a real second consumer or equivalent evidence; capability-specific output semantics remain separate.

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

Slice rule: inspect the actual legacy owner before extraction; characterize behavior first; prefer bounded capabilities with explicit dependency/native/security risk; preserve one-owner direct API + workflow architecture; use first-class Artifacts; classify PURE versus required publication explicitly; integrate diagnostics at real native/subprocess boundaries; keep orchestration separate from primitive transformation ownership.

### Slice 1 — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered ordered FILE_SET, PURE `files.literal`, canonical `packages/ktools-text/`, characterized Markdown/TXT merge, `text.merge.files` as NEVER, direct/workflow equivalence, ArtifactRegistry proof, centralized local URI parsing and hosted Text smoke.

Promotion `958d5bf563cda21673d69865d1508831c599c006` passed `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed `33631040505`.

### Slice 2 — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered `packages/ktools-pdf/`, explicit `pypdf>=5,<7`, checked PDF reader/error taxonomy, ordered page merge, atomic publication, progress-preserving direct API, `pdf.merge.files: FILE_SET -> PDF` version 1 NEVER, PDF Artifact/ArtifactRegistry provenance, source-cache/publication lifecycle proof, deterministic fixtures, hosted reopen verification and protected/encrypted fail-closed behavior.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` passed run `33651923578` 5/5.

### Slice 3 — PDF Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered `file.literal: -> FILE` PURE, shared local-file Artifact construction, `ktools_pdf.splitter.split_pdf_into_parts`, `pdf.split.parts: FILE -> FILE_SET` version 1 NEVER, balanced contiguous part planning, non-overwriting naming, per-part atomic publication, explicit partial-set failure semantics, output PDF Artifacts with strong nested snapshots, direct/workflow equivalence, cached-source/publication proof and hosted split→merge composition without PDF_SET.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` passed run `33656157870` 5/5.

### Slice 4 — Text Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered split-specific decode order `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`; pure balanced line-unit planning; canonical split owner; UTF-8 collision-safe publication; per-part atomic/partial-set failure contract; `text.split.parts: FILE -> FILE_SET` version 1 NEVER; FILE Artifact metadata/provenance; nested strong snapshots; cached-source/republication proof; direct/workflow equivalence; and hosted Text split→merge composition in all Python lanes.

Evidence:

- spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`;
- RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`;
- GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`;
- hardened candidate `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`;
- terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

Canonical owner: `packages/ktools-text`. Stable-GUI Text merge/split remain compatibility debt.

### Slice 5 — Mixed Document Split Orchestrator V1

Status: **RESOLVED / PROMOTION CLOSURE GATE**

Fresh discovery selected the mixed Document Split boundary only after proving that its remaining product behavior is orchestration over already-canonical Text/PDF splitters.

Delivered:

- `packages/ktools-documents` depending on core/text/pdf only;
- structured `DocumentSplitBatchResult` and classified batch error;
- existing `.md/.txt/.pdf` filtering and ordered dispatch;
- equal progress span per compatible source;
- per-source error continuation and product-visible partial-success report;
- zero-successful-output failure;
- preservation of child Artifacts/types/MIME/metadata;
- current orchestrator run/node provenance and ArtifactRegistry snapshots;
- direct API and `document.split.files: FILE_SET -> FILE_SET + JSON`, version 1 NEVER;
- cached-upstream/republication proof;
- structural guard that forbids Text/PDF primitive logic in the documents pack;
- real mixed Text/PDF hosted workflow smoke on Ubuntu/Windows Python 3.10/3.13.

Evidence:

- spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / run `33661964413`, 5/5;
- RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / run `33662320157`, discriminating at the absent Documents product boundary after prior suites passed;
- GREEN/audited candidate `bde8b3789d86959b1218969510ed68aed14d410e` / run `33664355218`, 5/5.

ADR: `docs/decisions/ADR-027-DOCUMENT-SPLIT-ORCHESTRATOR-V1.md`.
Canonical batch owner: `packages/ktools-documents`; primitive owners remain `ktools-text` and `ktools-pdf`.
Stable-GUI mixed Document Split becomes compatibility debt.

### Slice 6 — FRESH DISCOVERY GATE

Status: **PENDING TERMINAL SLICE-5 MEMORY CI**

After the Slice-5 memory closure itself is green, re-inspect remaining real owners and compare at minimum:

- Images→PDF;
- WebP→PNG;
- bounded Files/Folders operations.

Decision dimensions:

- behavior clarity and characterization cost;
- dependency/security/native coupling;
- side effects/publication semantics;
- Artifact/typed-port cardinality;
- cacheability/output validity;
- diagnostics needs;
- composition value;
- duplicate-owner migration cost.

Image rule: before any image implementation, lock Pillow dependency range plus decompression-bomb limits/warnings, EXIF orientation policy, color/mode normalization, transparency/background policy, animated/multi-frame behavior, collision/publication semantics and Artifact typing.

Files/Folders rule: bound traversal before coding — root validity, include files/dirs, hidden handling, recursion, symlink/reparse behavior, deterministic ordering, permission/OSError aggregation, report schema and whether the operation is pure observation or publishes reports.

Media rule: before broad audio/video nodes, establish one shared FFmpeg/FFprobe process boundary using M3 subprocess diagnostics and explicit M4 Artifact/cache semantics.

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

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in DoD. Every cacheable capability justifies purity, semantic identity and output validity explicitly. Every file cardinality remains honest; avoid collection conventions that hide singular semantics. Every multi-output capability states its transaction boundary explicitly. Orchestration layers preserve child owners rather than becoming duplicate transformation owners.

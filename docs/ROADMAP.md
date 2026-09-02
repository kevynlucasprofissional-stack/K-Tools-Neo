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
- Images/PDF;
- Media.

Slice rule: inspect the actual legacy owner before extraction; characterize behavior first; prefer bounded capabilities with explicit dependency/native/security risk; preserve one-owner direct API + workflow architecture; use first-class Artifacts; classify PURE versus required publication explicitly; integrate diagnostics at real native/subprocess boundaries.

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

Delivered:

- `file.literal: -> FILE`, version 1, PURE;
- shared local-file Artifact construction with `files.literal`;
- `ktools_pdf.splitter.split_pdf_into_parts` as one split owner;
- `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- balanced contiguous part planning with clamp to page count;
- non-overwriting collision-safe part naming;
- per-part atomic publication and explicit partial-set failure contract;
- output PDF Artifacts with provenance/page-range metadata + strong nested snapshots;
- direct/workflow equivalence;
- cached source + required publication proof;
- real hosted `file.literal -> pdf.split.parts -> pdf.merge.files` composition on every Python lane;
- explicit decision to keep FILE_SET with typed PDF members rather than invent PDF_SET.

Evidence:

- spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704` / `33652921999`;
- RED `e43f01db3473aa693382325e70fc7e1c17d1943d` / `33653225831`;
- GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925` / `33653824159`, 5/5;
- technical candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e` / `33654265424`, 5/5 including split→merge smoke.

Canonical owner: `packages/ktools-pdf`. Stable-GUI PDF merge/split remain compatibility debt.

### Slice 4 — FRESH DISCOVERY GATE

Status: **PENDING TERMINAL SLICE-3 CI**

After the Slice-3 memory closure itself is green, re-inspect remaining actual owners and compare:

- Images→PDF;
- WebP→PNG;
- mixed Document Split;
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

Do not select merely to maximize node count.

A likely sequencing advantage now exists for mixed Document Split because both canonical Text and PDF primitives are available, but that hypothesis must be compared against the other candidates rather than assumed.

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

Take the first unresolved milestone/slice whose prerequisites are satisfied and work through explicit discovery → spec → evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure.

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in DoD. Every cacheable capability justifies purity, semantic identity and output validity explicitly. Every file cardinality remains honest; avoid collection conventions that hide singular semantics.

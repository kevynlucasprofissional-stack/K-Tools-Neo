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

Slice rule: inspect the actual legacy owner before extraction; characterize behavior first; prefer bounded capabilities with explicit dependency/native risk; preserve one-owner direct API + workflow architecture; use first-class Artifacts; classify PURE versus publication side effects explicitly; integrate diagnostics at the real boundary.

### Slice 1 — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered ordered FILE_SET, PURE `files.literal`, canonical `packages/ktools-text/`, characterized Markdown/TXT merge, `text.merge.files` as NEVER, direct/workflow equivalence, ArtifactRegistry proof, centralized local URI parsing and hosted Text smoke.

Promotion merge `958d5bf563cda21673d69865d1508831c599c006` passed run `33630159514`; final memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed `33631040505`.

### Slice 2 — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered:

- `packages/ktools-pdf/` with explicit `pypdf>=5,<7`;
- checked PDF reader/error taxonomy;
- ordered page merge + safe atomic publication;
- progress-preserving direct API;
- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- PDF Artifact/ArtifactRegistry provenance;
- source-cache + required-publication lifecycle proof;
- deterministic generated PDF fixtures;
- hosted PDF workflow smoke + reopened page-order assertion;
- fail-closed protected/encrypted behavior;
- no duplicate URI parser or reader/page-copy implementation in adapter.

Evidence:

- spec `081dac1380361761bf38e2914db495138e4c9b76` / run `33631531313`;
- RED `29a90cb7c2085b22d0cf3e345b39fecb6c050b76` / run `33648993271`;
- GREEN `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25` / run `33649227197` 5/5;
- technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c` / run `33649789491` 5/5;
- synchronized memory candidate `8600b0adda1bba2a460da9fee8f45b7a02b41f9b` / run `33650661761` 5/5.

Canonical owner: `packages/ktools-pdf`. Stable-GUI PDF merge remains compatibility debt.

### Slice 3 — ACTIVE DISCOVERY

Status: **UNSELECTED**

Re-inspect remaining real owners. Current candidate set:

- PDF split;
- Images→PDF;
- WebP→PNG;
- mixed document split;
- bounded Files/Folders operations.

Compare each on behavior clarity, dependency/native coupling, side effects/publication semantics, Artifact/typed-port shape, cacheability/validity, diagnostics needs, composition value and duplicate-owner migration cost. Do not select merely to maximize node count.

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

Take the first unresolved milestone/slice whose prerequisites are satisfied and work through explicit spec → evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure.

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in DoD. Every cacheable capability justifies purity, semantic identity and output validity explicitly.

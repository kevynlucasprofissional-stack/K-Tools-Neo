# Current State — K-Tools Neo

## Current development truth

`main` is the single active development/integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.
Canonical sequencing guide: `docs/ROADMAP.md`.
OpenCode, Antigravity and Codex remain paused as active writers unless explicitly re-enabled.

## M0 — Platform Foundation — RESOLVED / PROMOTED

UI-independent Python core runtime, typed node/port contracts, deterministic DAG validation/execution, Artifact model, CLI and Windows/Linux CI are established.

## M1 — First official Node Pack — RESOLVED

`packages/ktools-json/` proves one capability owner shared by direct API and workflow use. Official JSON nodes include PURE planning/source nodes and NEVER publication where side effects are required.

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` remains audited evidence that React + `@xyflow/react` can own graph interaction while `ktools-core` remains runtime authority.

## M2 — Durable Execution V1 — RESOLVED

Optional RunJournal + Memory/SQLite persistence provide ordered run/node history, projections, failure/output metadata and interruption reconciliation.

## M3 — Diagnostics + Support Bundle — RESOLVED / PROMOTED

Structured/share-safe diagnostics, support reports/bundles, subprocess/PowerShell capture, redaction, interruption handling and abandoned-session packaging are established.

Final closure `5e1e46714aaefe0827c96a415d7d58d57790a187`, run `33557338124`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1 — RESOLVED / PROMOTED

Strong local-file validity, Artifact occurrence provenance, explicit versioned cache policy, semantic signatures, persistent fail-open cache, CACHED lifecycle truth and conservative restart reuse are established.

Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1`, run `33626260487`.

## Runtime invariants

```text
WorkflowEngine
  ├─ RunJournal
  ├─ DiagnosticsSession
  ├─ NodeCache
  └─ ArtifactRegistry
```

All remain optional injected concerns.

Carry-forward invariants:

- prior success alone never proves safe reuse;
- cacheability is capability-owned and defaults conservative;
- required publication side effects are not skipped without a proved replay contract;
- CACHED is distinct from executed success;
- unfinished persisted state is not proof of process death;
- diagnostics is part of DoD for significant native/subprocess/integration work;
- direct Tool/API and workflow routes share one business-logic owner;
- shared platform boundaries such as local file URI resolution live in core rather than being recopied per pack;
- user output files are not automatically deleted merely because metadata/cache is invalidated;
- singular and collection cardinality remain explicit (`FILE` is not a one-item `FILE_SET` convention);
- domain-specific collection types are introduced only when a real graph-time requirement proves them necessary;
- multi-output publication must state whether its transaction boundary is per output or set-wide;
- compatibility copies in the legacy GUI are frozen once a canonical package owner is promoted.

## M5 — Official local Node Packs — ACTIVE / ITERATIVE DELIVERY

### Slice 1 — Text Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for Markdown/TXT merge. FILE_SET, `files.literal`, characterized merge behavior, Artifact provenance, source invalidation and hosted Text workflow smoke are proved.

Promotion `958d5bf563cda21673d69865d1508831c599c006`, run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`.

### Slice 2 — PDF Merge Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is canonical for PDF merge.

Delivered checked PDF reading, ordered merge, safe atomic publication, progress-preserving direct API, `pdf.merge.files: FILE_SET -> PDF` version 1 NEVER, PDF Artifact provenance/strong snapshots, source-cache/publication proof, deterministic fixtures, semantic reopen verification and fail-closed protected/encrypted behavior.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5.

### Slice 3 — PDF Split Node V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is canonical for balanced PDF split as well as merge.

Delivered `file.literal: -> FILE` PURE, shared local-file Artifact construction, `splitter.split_pdf_into_parts`, `pdf.split.parts: FILE -> FILE_SET` version 1 NEVER, balanced contiguous partitioning with clamp, collision-safe naming, per-part atomic writes, explicit partial-set failure semantics, PDF Artifact provenance/page-range metadata, nested strong snapshots, cache/publication proof, direct/workflow equivalence and hosted split→merge composition without PDF_SET.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a`, run `33656157870`, 5/5.

### Slice 4 — Text Split Node V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is now canonical for balanced Markdown/TXT split as well as merge.

Delivered:

- split-specific legacy decode policy `utf-8-sig -> utf-8 -> cp1252 -> latin-1` without changing Text Merge decoding;
- pure `split_text_balanced(...)` line-unit planner;
- `split_text_file_into_parts(...)` as one split owner;
- UTF-8 output normalization and collision-safe naming;
- reusable Text-pack atomic text-content publication;
- direct API + thin `text.split.parts` adapter;
- `text.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- FILE Artifact MIME/provenance/chunk metadata;
- nested ArtifactRegistry strong snapshots;
- cached `file.literal` + required re-publication proof;
- forced later-part failure boundary;
- direct/workflow byte equivalence;
- ordered `file.literal -> text.split.parts -> text.merge.files` composition;
- hosted Text split→merge smoke in every Python lane.

Evidence chain:

- spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa`, run `33656954591`, 5/5;
- RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e`, run `33657352636`, discriminating at Text Split product contracts;
- GREEN `87558e8194692c045bdd95780fe05beb0f436e3a`, run `33657882057`, 5/5;
- hardened candidate `0630e63d87ae1c452c3d886a2dbab8d994bb3b23`, run `33660594733`, 5/5 including Text split→merge smoke.

ADR: `docs/decisions/ADR-026-TEXT-SPLIT-NODE-V1.md`.
Evidence/final report: `docs/specs/text-split-node-v1/`.

Historical stable-GUI Text merge/split implementations remain frozen compatibility debt; semantic evolution belongs to `ktools-text`.

### Slice 5 — PENDING FRESH DISCOVERY

Both primitive branches used by the historical mixed Document Split are now canonical:

- PDF split -> `ktools-pdf`;
- Markdown/TXT split -> `ktools-text`.

Fresh discovery should therefore compare mixed Document Split orchestration against Images→PDF, WebP→PNG and bounded Files/Folders work. Do not assume Document Split automatically wins; inspect its real dispatch, aggregation, progress, naming and failure contract first.

## Next exact action

Require this Slice-4 synchronized memory-closure HEAD itself to pass the standard 5-job hosted CI gate. If green, begin Slice 5 discovery from that exact terminal `main` state and continue discovery -> spec -> RED -> GREEN -> REFACTOR -> hosted evidence -> memory closure.

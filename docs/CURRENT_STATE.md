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
- domain-specific collection types are introduced only when a real graph-time requirement proves them necessary.

## M5 — Official local Node Packs — ACTIVE / ITERATIVE DELIVERY

### Slice 1 — Text Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for Markdown/TXT merge. FILE_SET, `files.literal`, characterized merge behavior, Artifact provenance, source invalidation and hosted Text workflow smoke are proved.

Promotion merge `958d5bf563cda21673d69865d1508831c599c006`, run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`.

### Slice 2 — PDF Merge Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is canonical for PDF merge.

Delivered checked PDF reading, ordered merge, safe atomic publication, progress-preserving direct API, `pdf.merge.files: FILE_SET -> PDF` version 1 NEVER, PDF Artifact provenance/strong snapshots, source-cache/publication proof, deterministic fixtures, semantic reopen verification and fail-closed protected/encrypted behavior.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5.

### Slice 3 — PDF Split Node V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is now canonical for balanced PDF split as well as merge.

Delivered:

- `file.literal: -> FILE`, version 1, PURE;
- shared single/multi local-file Artifact construction;
- `splitter.split_pdf_into_parts` as the single split implementation owner;
- direct API + thin `pdf.split.parts` adapter;
- `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- balanced contiguous partitioning with page-count clamp;
- collision-safe `{stem}_parte_XX_de_YY.pdf` publication;
- per-part atomic writes and explicit partial-set failure semantics;
- protected/corrupt/empty fail-closed behavior;
- PDF Artifact provenance, MIME and page-range metadata;
- nested ArtifactRegistry strong snapshots;
- proof that cached `file.literal` does not suppress required split publication;
- direct/workflow equivalence;
- real `file.literal -> pdf.split.parts -> pdf.merge.files` hosted composition without introducing PDF_SET.

Evidence chain:

- spec `a09d600924aa66d031cc2bcc2f59feb04bdf0704`, run `33652921999`, 5/5;
- RED `e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`, discriminating at new PDF split contracts;
- GREEN `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925`, run `33653824159`, 5/5;
- hardened technical candidate `cb25cad6e6d60377d07a0c4d761700d7785f0c1e`, run `33654265424`, 5/5 including split→merge smoke on every Python lane.

ADR: `docs/decisions/ADR-025-PDF-SPLIT-NODE-V1.md`.
Evidence/final report: `docs/specs/pdf-split-node-v1/`.

Historical stable-GUI PDF merge/split implementations remain frozen compatibility debt; semantic evolution belongs to `ktools-pdf`.

### Slice 4 — PENDING FRESH DISCOVERY

Do not preselect by node count. Re-inspect remaining owners after PDF split is terminal-green. Current candidate set includes:

- Images→PDF;
- WebP→PNG;
- mixed Document Split now that Text/PDF primitives are canonical;
- bounded Files/Folders operations.

Compare behavior clarity, dependency/security boundary, side effects, Artifact/typed-port shape, diagnostics needs, composition value and duplicate-owner migration cost.

## Next exact action

Require this Slice-3 memory-closure HEAD itself to pass the standard 5-job hosted CI gate. If green, begin Slice 4 fresh discovery from that exact terminal `main` state, then continue spec → RED → GREEN → REFACTOR → hosted evidence → memory closure.

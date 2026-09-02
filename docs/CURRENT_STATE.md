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
- compatibility copies in the legacy GUI are frozen once a canonical package owner is promoted;
- cross-pack orchestration preserves child capability ownership and returned domain Artifacts rather than copying primitive algorithms;
- third-party image decoding has an explicit safety/version policy before broad image capabilities depend on it;
- image format semantics may stay in member Artifact metadata while `FILE_SET` remains the collection port until a real graph-time requirement proves otherwise.

## M5 — Official local Node Packs — ACTIVE / ITERATIVE DELIVERY

### Slice 1 — Text Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for Markdown/TXT merge. FILE_SET, `files.literal`, characterized merge behavior, Artifact provenance, source invalidation and hosted Text workflow smoke are proved.

Promotion `958d5bf563cda21673d69865d1508831c599c006`, run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505`.

### Slice 2 — PDF Merge Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is canonical for PDF merge. Checked reading, ordered merge, safe atomic publication, direct API, `pdf.merge.files: FILE_SET -> PDF` v1 NEVER, PDF Artifact provenance/snapshots, cache/publication proof and protected/encrypted fail-closed behavior are hosted-tested.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8`, run `33651923578`, 5/5.

### Slice 3 — PDF Split Node V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is canonical for balanced PDF split. `file.literal`, `pdf.split.parts: FILE -> FILE_SET` v1 NEVER, balanced page planning, collision-safe per-part atomic publication, explicit partial-set failure, PDF Artifact page metadata, snapshots, cache/publication proof and split→merge composition are hosted-tested.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a`, run `33656157870`, 5/5.

### Slice 4 — Text Split Node V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for balanced Markdown/TXT split. Split-specific decode policy, balanced line planning, UTF-8 collision-safe per-part publication, `text.split.parts: FILE -> FILE_SET` v1 NEVER, Artifact metadata/snapshots, cached-source/republication proof and split→merge composition are hosted-tested.

Evidence: spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`; RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`; GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`; hardened `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`; terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

### Slice 5 — Mixed Document Split Orchestrator V1 — RESOLVED / PROMOTED

`packages/ktools-documents/` is canonical for mixed `.md/.txt/.pdf` batch orchestration only; primitive Text/PDF split behavior remains in `ktools-text` and `ktools-pdf`.

Delivered supported-input filtering, ordered dispatch, equal source progress spans, per-source continuation, product-visible partial-success report, zero-success failure, exact child Artifact preservation, coherent provenance/snapshots, direct API and `document.split.files: FILE_SET -> FILE_SET + JSON` v1 NEVER, cached-upstream/republication proof and hosted mixed Text/PDF smoke.

Evidence: spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`; RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`; GREEN `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`; terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.

ADR: `docs/decisions/ADR-027-DOCUMENT-SPLIT-ORCHESTRATOR-V1.md`.
The stable GUI mixed dispatcher is frozen compatibility debt.

### Slice 6 — Image Safety Foundation + WebP→PNG V1 — RESOLVED / PROMOTION CLOSURE GATE

`packages/ktools-images/` is now the canonical evolution owner for the image-safety foundation and WebP→PNG conversion.

Delivered:

- `Pillow>=12,<13` package boundary;
- 80,000,000-pixel/decompression-bomb policy;
- EXIF orientation normalization;
- explicit animated WebP frame-0 policy;
- transparency preservation as RGBA PNG where applicable;
- RGB/L preservation and fallback RGB normalization;
- collision-safe per-output temp→promote publication;
- explicit non-transactional batch failure boundary;
- one canonical converter owner shared by direct API and node;
- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1, NEVER;
- IMAGE Artifacts with PNG MIME, current provenance and image-policy metadata;
- ArtifactRegistry strong snapshots;
- cached `files.literal` without suppressed re-publication;
- real generated RGB/RGBA hosted workflow smoke in every Python lane.

Evidence:

- spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3`, run `33666227293`, 5/5;
- discriminating RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc`, run `33667224304`;
- GREEN/audited candidate `670a503d822ba100a66eea3ba0b31cfe39692984`, run `33667874076`, 5/5.

ADR: `docs/decisions/ADR-028-IMAGE-SAFETY-WEBP-PNG-V1.md`.
Evidence/final report: `docs/specs/webp-to-png-node-v1/`.
The stable GUI WebP→PNG path is now compatibility debt; semantic evolution belongs to `ktools-images`.

### Slice 7 — PENDING FRESH DISCOVERY

Remaining bounded candidates now include at minimum:

- Images→PDF, which has sequencing advantage because canonical image safety/EXIF/frame policy now exists;
- bounded Files/Folders operations, which still require a cross-platform traversal/result contract.

Do not auto-select Images→PDF solely because the shared foundation exists. Re-inspect the exact terminal `main` after the Slice-6 closure HEAD is green and compare behavior clarity, security/dependencies, publication semantics, Artifact cardinality, cacheability, composition value and duplicate-owner reduction.

If Images→PDF wins, it must reuse `ktools-images` safety/orientation policy while specifying its own supported formats, ordered pages, RGB conversion, alpha→white background behavior, multi-frame policy, singular PDF Artifact, aggregate publication and NEVER/cache semantics.

If Files/Folders wins, lock root validity, files/dirs inclusion, hidden handling, recursion, symlink/reparse behavior, deterministic ordering, permission/OSError aggregation, report schema and observation/publication ownership before implementation.

## Next exact action

Require this synchronized Slice-6 memory-closure HEAD itself to pass the standard five hosted jobs. If green, Slice 6 becomes terminally **RESOLVED / PROMOTED** and Slice 7 begins fresh discovery from that exact `main` state.

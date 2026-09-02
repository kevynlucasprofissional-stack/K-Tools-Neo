# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.
Canonical sequencing guide: `docs/ROADMAP.md`.
OpenCode, Antigravity and Codex remain paused as active writers unless explicitly re-enabled.

## M0 — Platform Foundation — RESOLVED / PROMOTED

UI-independent core runtime, typed node/port contracts, deterministic DAG validation/execution, initial Artifact model, CLI and Windows/Linux CI are established.

## M1 — First official Node Pack — RESOLVED

`packages/ktools-json/` proves one capability owner shared by direct API and workflow use. Official JSON nodes include `json.literal` (PURE), `json.split.plan` (PURE) and `json.split` (NEVER).

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` remains audited evidence for React + `@xyflow/react` as interaction layer while `ktools-core` remains runtime authority.

## M2 — Durable Execution V1 — RESOLVED

Optional RunJournal + Memory/SQLite persistence provide ordered run/node history, projections, failure/output metadata and interruption reconciliation.

## M3 — Diagnostics + Support Bundle — RESOLVED / PROMOTED

Structured/share-safe diagnostics, support reports/bundles, subprocess/PowerShell capture, tracebacks, decisions/metrics/batches/anomalies, redaction, interruption handling and abandoned-session packaging are established.

Final closure: `5e1e46714aaefe0827c96a415d7d58d57790a187`, run `33557338124`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1 — RESOLVED / PROMOTED

Strong local-file validity, Artifact occurrence provenance, versioned explicit cache policy, semantic signatures, persistent fail-open cache, CACHED lifecycle truth and conservative restart reuse are established.

Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

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
- publication side effects are never skipped without a proved replay contract;
- CACHED is distinct from executed success;
- unfinished persisted state is not proof of process death;
- diagnostics is part of DoD for significant native/subprocess/integration work;
- direct Tool/API and workflow routes share one business-logic owner;
- shared platform boundaries such as local file URI resolution live in core rather than being recopied per pack;
- user output files are not automatically deleted merely because metadata/cache is invalidated.

## M5 — Official local Node Packs — ACTIVE / ITERATIVE DELIVERY

### Slice 1 — Text Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for Markdown/TXT merge. FILE_SET, `files.literal`, characterized merge behavior, Artifact provenance, source invalidation and hosted Text workflow smoke are proved.

Promotion merge `958d5bf563cda21673d69865d1508831c599c006` passed run `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed `33631040505`.

### Slice 2 — PDF Merge Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-pdf/` is now canonical for PDF merge.

Delivered:

- explicit `pypdf>=5,<7` dependency boundary;
- checked reader + `PdfMergeError`;
- ordered page merge and safe temp-then-replace publication;
- direct API with progress forwarding;
- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- PDF Artifact metadata/provenance + ArtifactRegistry strong snapshot;
- proof that cached `files.literal` does not suppress merge publication;
- generated deterministic fixtures and semantic direct/workflow equivalence;
- real hosted PDF workflow smoke with reopened page-order verification;
- protected/encrypted inputs fail closed without implicit decryption dependency;
- adapter reuses core URI parsing and contains no PDF reader/page-copy algorithm.

Evidence chain:

- spec gate `081dac1380361761bf38e2914db495138e4c9b76`, run `33631531313` green;
- RED `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271` discriminating at PDF tests;
- GREEN `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`, run `33649227197` 5/5;
- technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491` 5/5 including PDF smoke;
- synchronized memory candidate `8600b0adda1bba2a460da9fee8f45b7a02b41f9b`, run `33650661761` 5/5.

Historical stable-GUI PDF merge remains frozen compatibility debt; semantic evolution belongs to `ktools-pdf`.

Evidence/final report: `docs/specs/pdf-merge-node-pack-v1/`.

### Slice 3 — ACTIVE DISCOVERY

No capability is preselected. Re-inventory remaining owners and compare PDF split, Images→PDF, WebP→PNG, mixed document split and bounded Files/Folders operations on dependency/native risk, side effects, Artifact shape, cacheability, diagnostics needs, composition value and duplicate-owner migration cost.

## Next exact action

Require the terminal-state documentation HEAD to remain green, then lock M5 Slice 3 only after fresh discovery. Continue RED → GREEN → REFACTOR → hosted evidence → memory closure without broad GUI rewrites.

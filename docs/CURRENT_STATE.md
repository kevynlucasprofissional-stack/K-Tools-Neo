# Current State — K-Tools Neo

## Current development truth

`main` is the single active development and integration truth.

Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`.

Canonical sequencing guide: `docs/ROADMAP.md`.

OpenCode, Antigravity and Codex remain paused as active writers unless the project owner explicitly re-enables them.

## M0 — Platform Foundation — RESOLVED / PROMOTED

UI-independent `ktools-core`, typed node/port contracts, deterministic DAG validation/execution, initial Artifact model, CLI, Windows/Linux CI and bounded imported application subsystems are established.

## M1 — First official Node Pack — RESOLVED

`packages/ktools-json/` proves one capability owner shared by direct API and workflow use. Current official JSON nodes include `json.literal` (PURE), `json.split.plan` (PURE) and `json.split` (NEVER because file publication is a required side effect).

## AG-001 — xyflow interaction spike — CLOSED

`spikes/xyflow-editor/` remains evidence that React + `@xyflow/react` is a credible interaction layer while `ktools-core` remains execution truth.

## M2 — Durable Execution V1 — RESOLVED

Optional injected Run Journal + stdlib SQLite persistence provide ordered run/node lifecycle history, query projections, error/output metadata, explicit interruption reconciliation and `--journal` support.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

## M3 — Diagnostics, Structured Logging + Support Bundle — RESOLVED / PROMOTED

K-Tools has structured diagnostics, safe-sharing redaction, exceptions/tracebacks, decisions/metrics/batches/anomalies, subprocess capture, PowerShell evidence, automatic human/machine support reports, support bundles, Ctrl+C classification and conservative abandoned-session packaging.

Final M3 closure checkpoint `5e1e46714aaefe0827c96a415d7d58d57790a187` passed run `33557338124`.

Evidence: `docs/specs/diagnostics-support-bundle-v1/`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1 — RESOLVED / PROMOTED

M4 adds local file Artifact snapshots with SHA-256 validity, persistent Artifact occurrence/provenance, versioned explicit cache policy, stable semantic signatures, persistent fail-open SQLite cache, cached-output revalidation, explicit CACHED lifecycle truth, cache diagnostics, CLI cache/Artifact-registry surfaces and conservative restart recovery as new run + validated PURE reuse.

Accepted code candidate `c7ae2fa3953099d0bd9377da7c2c0195e96f6175` passed run `33560041360`; canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed run `33625955613`; formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

Evidence/final report: `docs/specs/artifact-recovery-cache-v1/`.

## Runtime architecture now

```text
WorkflowEngine
  ├─ RunJournal          -> lifecycle truth/history
  ├─ DiagnosticsSession  -> forensic/support evidence
  ├─ NodeCache           -> validated reusable PURE results
  └─ ArtifactRegistry    -> Artifact occurrence/validity provenance
```

All four remain optional injected concerns rather than hidden global runtime dependencies.

Typed file composition includes `FILE` for one file Artifact and `FILE_SET` for an ordered list/tuple of FILE Artifacts.

Carry-forward invariants:

- previous success is not sufficient for reuse;
- cacheability is explicit and capability-owned;
- side effects are never skipped without a proved replay/publication contract;
- cache/Artifact-registry failures remain supplemental where normal execution can proceed;
- `CACHED` is distinct from executed success;
- unfinished persisted state is not proof of process death;
- user output files are not automatically deleted from metadata invalidation;
- diagnostics is part of Definition of Done for significant native/subprocess/integration work;
- direct Tool/API and workflow routes share one capability owner rather than duplicate business logic;
- shared platform boundaries such as local `file://` interpretation stay in `ktools-core` rather than being recopied per pack.

## Active roadmap milestone — M5 Official local Node Packs

Status: **ACTIVE — ITERATIVE DELIVERY**.

### Slice 1 — Text Node Pack V1 — RESOLVED / PROMOTED

`packages/ktools-text/` is canonical for Markdown/TXT merge. `FILE_SET`, `files.literal`, byte-equivalent supported merge behavior, Artifact provenance, cache/source invalidation and hosted Text workflow smoke are proven.

RED: `1660a4dbac7efc7f21d7a96bfdebde8ffc13edd2`, run `33626957901`.
Promotion merge: `958d5bf563cda21673d69865d1508831c599c006`, post-merge run `33630159514` success.
Final memory closure: `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`, run `33631040505` success.

Historical GUI merge code remains explicit compatibility debt; semantic evolution belongs to `ktools-text`.

Evidence/final report: `docs/specs/text-node-pack-v1/`.

### Slice 2 — PDF Merge Node Pack V1 — IMPLEMENTATION ACCEPTED / FINAL MEMORY CI PENDING

Selected after comparing bounded PDF/image/document owners.

Implemented:

- explicit `packages/ktools-pdf/` dependency boundary with `pypdf>=5,<7`;
- checked reader + `PdfMergeError` taxonomy;
- ordered page merge and same-directory atomic publication;
- direct API with progress callback forwarding;
- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- output PDF Artifact with source/page metadata and run/node provenance;
- ArtifactRegistry strong snapshot;
- proof that cached `files.literal` does not skip PDF publication;
- generated fixture PDFs for semantic direct/workflow equivalence;
- real root-CI PDF workflow smoke + reopen/page-order verification;
- local URI parsing reused from `ktools-core`;
- encrypted PDFs fail closed in V1 without implicit cryptography/decryption policy.

Spec gate: `081dac1380361761bf38e2914db495138e4c9b76`, run `33631531313` green.
RED: `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271` reached PDF tests after dependencies and existing suites passed.
Initial GREEN: `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25`, run `33649227197` 5/5.
Accepted technical candidate: `a370028b9dbb2c44981a3c7e05d176ce7e54b71c`, run `33649789491` 5/5 including PDF smoke in all Python lanes.

Canonical owner after final closure: `packages/ktools-pdf/`. The stable GUI copy remains compatibility debt, not an independent semantic owner.

Evidence/final report: `docs/specs/pdf-merge-node-pack-v1/`.

## Next exact action

Run the five-job hosted matrix on the synchronized PDF Slice 2 memory-closure HEAD. If green, mark PDF Merge V1 RESOLVED / PROMOTED, then re-inventory remaining legacy owners and select M5 Slice 3 through evidence rather than convenience.

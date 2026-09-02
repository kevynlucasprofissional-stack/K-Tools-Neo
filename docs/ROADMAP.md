# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

## Product destination

K-Tools Neo becomes one integrated local-first product where every reusable operation is a capability/node, simple Tools and visual Workflows share implementation owners, expensive/local work is observable/durable/diagnosable/conservatively reusable, official Node Packs cover local capability families, imported applications are adapted rather than rewritten, the UI is a client of stable runtime contracts, and later AI agents compose through the same catalog.

---

## M0 — Platform Foundation

Status: **RESOLVED / PROMOTED**

Delivered UI-independent core runtime, typed validation/execution, initial Artifact model, CLI, hosted CI and architecture memory.

---

## M1 — First real Node Pack

Status: **RESOLVED**

Delivered `packages/ktools-json/` with one-owner direct API/workflow implementation, classified failures, collision safety and hosted evidence.

---

## M2 — Durable Execution V1

Status: **RESOLVED**

Delivered optional Run Journal, ordered lifecycle events, Memory/SQLite journals, run/node projections, error/output metadata, interruption reconciliation, query API and `--journal`.

---

## M3 — Diagnostics, Structured Logging + Support Bundle

Status: **RESOLVED / PROMOTED**

Delivered structured/share-safe diagnostics, support reports/bundles, subprocess and PowerShell evidence, interruption handling and conservative abandoned-session packaging.

Final closure run: `33557338124` on `5e1e46714aaefe0827c96a415d7d58d57790a187`.

---

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **RESOLVED / PROMOTED**

Delivered persistent Artifact provenance/validity observations, SHA-256 strong local-file validity, versioned explicit cache policy, deterministic semantic signatures, persistent fail-open SQLite cache, cached-output revalidation, explicit CACHED lifecycle truth, cache diagnostics, CLI cache/Artifact-registry surfaces, a real official pure-workload cache proof and a conservative recovery/ownership boundary.

Code candidate `c7ae2fa3953099d0bd9377da7c2c0195e96f6175` passed run `33560041360`.
Canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed run `33625955613`.
Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

Evidence: `docs/specs/artifact-recovery-cache-v1/`.

---

## M5 — Official local Node Packs

Status: **ACTIVE / ITERATIVE DELIVERY**

Migrate real legacy functionality behind one-owner capability packages.

Capability families:

- Files/Folders;
- Text;
- Images/PDF;
- Media.

Slice rule: inspect the actual legacy owner before extraction; characterize existing behavior; prefer a bounded capability whose native/dependency risk is explicit; preserve direct Tool/API + workflow one-owner architecture; use first-class Artifacts where the file contract warrants it; classify PURE versus side-effectful behavior explicitly; integrate diagnostics at the real boundary.

### Slice 1 — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered ordered `FILE_SET`, PURE `files.literal` with M4 strong revalidation, `packages/ktools-text/`, characterized Markdown/TXT merge, `text.merge.files: FILE_SET -> FILE` as NEVER, direct/workflow byte equivalence, ArtifactRegistry proof, centralized local-file URI interpretation and hosted workflow verification.

Promotion merge `958d5bf563cda21673d69865d1508831c599c006` passed post-merge run `33630159514`. Final memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` passed run `33631040505`.

Canonical owner: `packages/ktools-text`. Historical GUI copy remains compatibility debt.

### Slice 2 — PDF Merge Node Pack V1

Status: **IMPLEMENTATION ACCEPTED / FINAL MEMORY CI PENDING**

Selected after re-inventorying PDF merge, PDF split, Images→PDF, WebP→PNG and mixed document split.

Delivered candidate:

- `packages/ktools-pdf/` with explicit `pypdf>=5,<7` dependency;
- checked reader and `PdfMergeError` domain taxonomy;
- ordered file/page merge with fail-closed protected/corrupt/empty handling;
- same-directory temp write then final replace;
- progress callback preserved through direct API;
- `pdf.merge.files: FILE_SET -> PDF`, version 1, NEVER;
- output PDF Artifact + ArtifactRegistry strong-snapshot proof;
- source cache may reuse `files.literal` while publication still executes;
- generated fixture PDFs for semantic direct/workflow equivalence;
- real hosted PDF workflow smoke and page-order reopen assertion;
- no duplicate URI parser or reader/page algorithm in the adapter.

Spec gate `081dac1380361761bf38e2914db495138e4c9b76` passed run `33631531313`.
RED `29a90cb7c2085b22d0cf3e345b39fecb6c050b76`, run `33648993271`, failed first at intentionally unimplemented PDF tests after packaging/dependency and existing suites passed.
Initial GREEN `cdce28caa6e7cc8b62cf2f55e32559a2ff8cfd25` passed run `33649227197` 5/5.
Accepted technical candidate `a370028b9dbb2c44981a3c7e05d176ce7e54b71c` passed run `33649789491` 5/5 including PDF smoke on Windows/Linux Python 3.10/3.13.

Canonical owner after final closure: `packages/ktools-pdf`. Historical GUI PDF merge remains explicit compatibility debt.

### Slice 3 — UNSELECTED / AFTER PDF CLOSURE

Status: **GATED ON SLICE 2 MEMORY CLOSURE**

After PDF Merge V1 closes, re-inspect remaining owners. Current candidates include PDF split, Images→PDF, WebP→PNG, mixed document split and bounded Files/Folders operations. Choose based on existing behavior clarity, dependency/native coupling, side effects, Artifact shape, cacheability/validity, diagnostics needs, composition value and duplicate-owner migration cost.

Do not choose merely to maximize node count.

Media rule: create one shared FFmpeg/FFprobe process boundary before broad audio/video nodes. It must use M3 subprocess diagnostics and explicit M4 Artifact/cache semantics.

---

## M6 — Imported application adapters

Status: **PLANNED**

Expose YT-DLP TUI and XCursos Runner through explicit adapters while preserving mature internals, native diagnostics and error taxonomies.

---

## M7 — Runtime Contract API for UI

Status: **PLANNED**

Publish machine-readable Node Pack/catalog/config/workflow/validation/run/artifact/diagnostic contracts before production editor work.

---

## M8 — Production Workflow Editor

Status: **PLANNED**

Build production editor from runtime contracts and audited xyflow lessons. Run/cache/warning/error/diagnostic state comes from runtime truth rather than frontend simulation.

---

## M9 — Ready-made Tools + Templates

Status: **PLANNED**

Project workflows as simple Tools without duplicate logic; simple Tool runs receive the same lifecycle/cache/Artifact/diagnostic semantics as visual workflows.

---

## M10 — Desktop Product / Packaging

Status: **PLANNED / DECISION GATED**

Choose/validate Windows-first desktop host after runtime/UI contracts are stable; installer/support diagnostics must expose startup, sidecar, filesystem and subprocess failures.

---

## M11 — Agent-first composition

Status: **LATER**

Natural-language workflow creation/repair uses the same catalog/validator/runtime. Record operational decisions and concise reasons, never private chain-of-thought.

---

## M12 — Release hardening

Status: **CONTINUOUS + FINAL RELEASE GATE**

Keep CI green, classify dependencies/licenses, remove duplicate legacy ownership, profile expensive workflows, preserve diagnostics, version workflows/Node Packs, review subprocess/path/secrets security and smoke installers on clean Windows environments.

---

## Execution rule

Take the first unresolved milestone/slice whose prerequisites are satisfied, create/update an explicit spec, work through evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure, then advance while capacity remains.

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in Definition of Done. Every cacheable capability justifies purity, semantic identity and output validity explicitly.

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

Canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed run `33625955613`, satisfying the promotion gate.

Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` also passed its hosted matrix in run `33626260487`.

Evidence: `docs/specs/artifact-recovery-cache-v1/`.

---

## M5 — Official local Node Packs

Status: **ACTIVE / DISCOVERY + ITERATIVE DELIVERY**

Migrate real legacy functionality behind one-owner capability packages.

Capability families:

- Files/Folders;
- Text;
- Images/PDF;
- Media.

First-slice rule: inspect the actual legacy owner before extraction; characterize existing behavior; prefer a small deterministic capability with low native coupling; preserve direct Tool/API + workflow one-owner architecture; use first-class Artifacts where the file contract warrants it; classify PURE versus side-effectful behavior explicitly; integrate diagnostics at the real boundary.

### Slice 1 — Text Node Pack V1

Status: **IMPLEMENTATION COMPLETE / PROMOTION GATE**

Delivered candidate:

- ordered `FILE_SET` contract without inventing an unnecessary collection class;
- minimal `files.literal` source, PURE with M4 strong output revalidation;
- `packages/ktools-text/` capability/writer/direct API/node adapter;
- characterized Markdown/TXT decoding (`utf-8-sig`, UTF-8, latin-1), separator and publication behavior;
- `text.merge.files: FILE_SET -> FILE`, NEVER because publication/replacement is a required side effect;
- byte-identical direct API/workflow output under equivalent config;
- first-class output Artifact + ArtifactRegistry proof;
- source-file mutation invalidates cached FILE_SET source output;
- centralized local-file URI interpretation in `ktools-core` after integration audit;
- root CI Text tests and real workflow output verification.

Accepted code candidate `dbd39a1119ce1557d802a115404f01a3f797d93e` passed all five jobs in run `33627879876`.

Promotion remains gated on synchronized canonical-memory exact-head CI, PR #8 merge and post-merge `main` verification.

Canonical owner after promotion: `packages/ktools-text`. The historical GUI copy remains temporary compatibility debt and must not receive independent semantic evolution.

### Next M5 slice

Status: **UNSELECTED / DISCOVERY AFTER TEXT PROMOTION**

Do not choose the next capability merely because it is easy to name. Re-inspect actual legacy owners and compare dependency/native coupling, side effects, Artifact shape, composability and one-owner migration cost. WebP→PNG and generic folder scanning remain candidates rather than commitments.

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

Take the first unresolved milestone whose prerequisites are satisfied, create/update an explicit spec, work through evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure, then advance while capacity remains.

Every significant runtime/subprocess/integration capability after M3 includes diagnostics in Definition of Done. Every cacheable capability justifies purity, semantic identity and output validity explicitly.

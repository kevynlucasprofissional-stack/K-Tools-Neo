# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

This roadmap defines preferred product sequencing. Repository evidence may split or reorder work; material changes must be recorded in `docs/DECISIONS.md` or the active spec.

## Product destination

K-Tools Neo becomes one integrated local-first product where:

- every reusable operation is a capability/node;
- simple ready-made Tools and visual Workflows call the same implementation owners;
- workflows are built visually from typed blocks;
- expensive/local tasks are observable, diagnosable, durable and conservatively reusable/recoverable;
- every real execution can produce a shareable diagnostic record sufficient to reconstruct what happened;
- official Node Packs cover files, text, JSON, images, PDFs, audio, video and integrations;
- mature imported applications are exposed through adapters instead of being needlessly rewritten;
- the desktop UI is a client of stable runtime contracts, not a second engine;
- later, an AI agent can compose/validate workflows through the same node catalog humans use.

---

## M0 — Platform Foundation

Status: **RESOLVED / PROMOTED**

Delivered UI-independent `ktools-core`, typed ports/validation, deterministic DAG execution, initial Artifact model, CLI, Windows/Linux CI and architecture memory.

---

## M1 — First real Node Pack

Status: **RESOLVED**

Delivered `packages/ktools-json/` with one-owner direct API/workflow implementation, classified failures, collision safety and hosted evidence.

---

## M2 — Durable Execution V1

Status: **RESOLVED**

Delivered optional Run Journal injection, ordered run/node lifecycle events, Memory/SQLite journals, run/node projections, error/output metadata, interruption reconciliation, query API and `--journal` support.

Evidence: `docs/specs/durable-execution-v1/evidence.md`.

---

## M3 — Diagnostics, Structured Logging + Support Bundle

Status: **RESOLVED / PROMOTED**

Delivered a cross-cutting diagnostic/support layer before complex native/integration work.

Working now:

- structured DEBUG/INFO/WARNING/ERROR/CRITICAL events;
- log/decision/metric/batch/anomaly/exception/subprocess/lifecycle event kinds;
- run/workflow/node/stage/batch correlation;
- stdlib Python logging bridge;
- exception traceback capture;
- recursive safe-sharing redaction for common credential patterns;
- subprocess command/duration/exit/stdout/stderr/timeout/launch-failure diagnostics;
- real PowerShell stdout/stderr hosted smoke;
- automatic `session.json`, `diagnostics.jsonl`, `report.json`, `report.md` and `support-bundle.zip`;
- human execution reconstruction and raw-log inventory;
- CLI diagnostics by default with `--diagnostics-dir` / `--no-diagnostics`;
- Ctrl+C classified as `INTERRUPTED`;
- conservative stale abandoned-session packaging as `ABANDONED_OR_INTERRUPTED`.

Final M3 closure run: `33557338124` on `5e1e46714aaefe0827c96a415d7d58d57790a187`, all five jobs success.

Evidence: `docs/specs/diagnostics-support-bundle-v1/`.

Architectural carry-forward: significant runtime/subprocess/integration capabilities after M3 integrate diagnostics as part of Definition of Done.

---

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **IMPLEMENTATION RESOLVED / FINAL MEMORY-HEAD CI PENDING**

Delivered/proved:

- persistent Artifact occurrence/provenance records tied to run/node/output port/value path;
- local file snapshots with size, mtime-ns and SHA-256;
- strong revalidation before cached file reuse;
- stable semantic signatures over node type/version, canonical config and semantic inputs;
- explicit `CachePolicy.NEVER` default and `PURE` opt-in;
- persistent stdlib SQLite node cache;
- fail-open cache behavior;
- invalidation on config/input/version/Artifact-content/output-validity changes;
- explicit `NODE_CACHED` / `NodeRunStatus.CACHED` lifecycle truth;
- M3 diagnostic reasons for cache hit/miss/bypass/invalidation/failure;
- first-party CLI `--cache` and `--artifact-registry` support;
- real JSON workload proof using `json.split.plan` over 2,000 records with cache close/reopen;
- proof that `json.split` remains side-effectful and executes again even when its source is CACHED;
- conservative restart recovery boundary: new run + validated PURE reuse;
- explicit prohibition of automatic continuation of old RUNNING work without process/session ownership;
- metadata-only retention boundary: no automatic deletion of user output files.

Accepted code SHA `c7ae2fa3953099d0bd9377da7c2c0195e96f6175`, hosted run `33560041360`, all five jobs green. Canonical ADR checkpoint `38c0dad7799334ac44477ecc5992d02e7bf46b04` also passed run `33560424024`.

Evidence: `docs/specs/artifact-recovery-cache-v1/`.

Promotion rule: M4 becomes RESOLVED/PROMOTED only when the synchronized canonical-memory HEAD also passes the complete hosted matrix.

---

## M5 — Official local Node Packs

Status: **NEXT AFTER M4 PROMOTION GATE / ITERATIVE**

Migrate real legacy functionality behind one-owner capability packages.

Preferred capability families:

- Files/Folders;
- Text;
- Images/PDF;
- Media.

Before selecting the first implementation slice, inspect actual legacy ownership and choose a small deterministic capability that proves the M0-M4 platform contracts without duplicating existing behavior.

For media work, create one shared FFmpeg/FFprobe process boundary before broad audio/video nodes. That boundary must use M3 subprocess diagnostics and must define M4 Artifact/cache semantics explicitly rather than hiding native side effects.

---

## M6 — Imported application adapters

Status: **PLANNED**

Expose YT-DLP TUI and XCursos Runner as explicit adapters while preserving their mature internals, native diagnostics and error taxonomies. Correlate child runs/logs into the K-Tools diagnostic bundle rather than replacing them.

---

## M7 — Runtime Contract API for UI

Status: **PLANNED**

Publish machine-readable Node Pack/catalog/config/workflow/validation/run/artifact/diagnostic contracts before production editor work.

---

## M8 — Production Workflow Editor

Status: **PLANNED**

Build the production editor from runtime contracts and audited xyflow lessons. Run state, cache state, warnings, errors and diagnostic links come from runtime truth rather than frontend simulation.

---

## M9 — Ready-made Tools + Templates

Status: **PLANNED**

Project workflows as simple Tools without duplicate business logic; simple Tool runs receive the same history, cache/Artifact semantics and diagnostic bundle capability as visual workflows.

---

## M10 — Desktop Product / Packaging

Status: **PLANNED / DECISION GATED**

Choose/validate the Windows-first desktop host after runtime/UI contracts are stable. Installer/support diagnostics must make it possible to report startup, sidecar, filesystem and subprocess failures.

---

## M11 — Agent-first composition

Status: **LATER**

Natural-language workflow creation/repair uses the same catalog/validator/runtime. Agent decisions that affect execution should be recordable as diagnostic decision events without exposing private chain-of-thought; record the operational decision and concise reason/evidence only.

---

## M12 — Release hardening

Status: **CONTINUOUS + FINAL RELEASE GATE**

Across all milestones: keep CI green, classify dependencies/licenses, remove duplicate legacy ownership, profile expensive workflows, preserve structured diagnostics, version workflows/Node Packs, review subprocess/path/secrets security and smoke installers on clean Windows environments.

---

## Execution rule

The active implementer normally takes the **first unresolved milestone whose prerequisites are satisfied**, creates/updates an explicit spec, works through evidence → RED → GREEN → REFACTOR → regression → hosted evidence → memory closure, then advances while capacity remains.

Every significant runtime/subprocess/integration capability after M3 integrates diagnostics in its Definition of Done. Every candidate for M4 cache reuse must separately justify purity, semantic identity and output validity; side effects are never skipped merely because previous output exists.

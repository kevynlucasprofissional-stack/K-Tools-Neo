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
- expensive/local tasks are observable, diagnosable, durable and recoverable;
- every real execution can produce a shareable diagnostic record sufficient to reconstruct what happened;
- official Node Packs cover files, text, JSON, images, PDFs, audio, video and integrations;
- mature imported applications are exposed through adapters instead of being needlessly rewritten;
- the desktop UI is a client of stable runtime contracts, not a second engine;
- later, an AI agent can compose/validate workflows through the same node catalog humans use.

---

## M0 — Platform Foundation

Status: **RESOLVED / PROMOTED**

Delivered: UI-independent `ktools-core`, typed ports/validation, deterministic DAG execution, initial Artifact model, CLI, Windows/Linux CI and architecture memory.

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
- full human execution reconstruction covering steps, lots, decisions, metrics, anomalies, subprocesses, errors, outputs and Run Journal lifecycle;
- CLI diagnostics enabled by default with `--diagnostics-dir` and `--no-diagnostics`;
- Ctrl+C classified as diagnostic `INTERRUPTED`;
- conservative stale abandoned-session recovery as `ABANDONED_OR_INTERRUPTED`.

Hosted acceptance: run `33556969496` on `9c14e073ec5f770ce9d03d031c4ca1820bcd6ce2`, all Windows/Linux Python lanes plus xyflow green. Representative Ubuntu/Python 3.13 lane: 33 core tests + 59 JSON tests, real PowerShell test executed and passed.

Evidence: `docs/specs/diagnostics-support-bundle-v1/`.

Architectural rule from this milestone: every significant new runtime/subprocess/integration capability should integrate diagnostics as part of Definition of Done rather than adding logs retroactively.

---

## M4 — Artifact Lifecycle + Recovery + Semantic Cache

Status: **NEXT / ACTIVE TARGET**

Build on M2 durable state and M3 diagnostics rather than inventing parallel state.

Targets:

- persistent Artifact provenance/validity records tied to run/node/output port;
- local file observations such as existence, size, modification/fingerprint evidence where relevant;
- stable workflow/node input/config/version signatures;
- explicit cacheability/side-effect policy per node/capability;
- selective reuse of valid prior outputs;
- invalidation when inputs/config/node version/artifact validity changes;
- safe restart/recovery semantics and process/session ownership rules;
- explicit `CACHED` / `RECOVERED` semantics only when evidence supports them;
- cleanup/retention policy for temporary/intermediate artifacts;
- M3 diagnostic events explaining every cache reuse, invalidation and recovery decision;
- real workload proof that reuse avoids meaningful repeated work without returning stale/missing artifacts.

M4 must not treat an old successful row as sufficient cache validity. External filesystem mutation/deletion and side-effectful nodes must be part of the model.

---

## M5 — Official local Node Packs

Status: **PLANNED / ITERATIVE**

Migrate real legacy functionality behind one-owner capability packages: Files/Folders, Text, Images/PDF and Media. Create one shared FFmpeg/FFprobe process boundary before broad media nodes; that boundary must use M3 diagnostics.

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

Build the production editor from runtime contracts and audited xyflow lessons. Run state, warnings, errors and diagnostic links come from runtime truth rather than frontend simulation.

---

## M9 — Ready-made Tools + Templates

Status: **PLANNED**

Project workflows as simple Tools without duplicate business logic; simple Tool runs receive the same history and diagnostic bundle capability as visual workflows.

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

Every new significant runtime/subprocess/integration capability after M3 should integrate diagnostics as part of its Definition of Done rather than adding logs retroactively.

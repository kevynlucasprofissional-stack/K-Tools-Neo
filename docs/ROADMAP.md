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

Status: **NEXT / ACTIVE TARGET**

Goal: whenever K-Tools behaves unexpectedly, produce enough structured evidence to reconstruct the execution instead of relying on screenshots, memory or a copied terminal fragment.

This is a cross-cutting platform capability and must exist before cache/recovery, broad media migration, subprocess-heavy adapters and production UI.

### Required diagnostic model

Every execution path that opts into the product runtime must be able to record structured events with at least:

- timestamp and stable execution/run correlation;
- severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`);
- category/source/component;
- current workflow/node/stage/batch identity when applicable;
- human message plus machine-readable context;
- exceptions with type/message/traceback where safe;
- decisions made by the system and the evidence/reason behind them;
- warnings/anomalies such as inconsistent output, unexpected counts, degraded model quality or validation mismatch;
- metrics/timings/counts needed to understand performance and behavior.

### Console / PowerShell / subprocess diagnostics

Provide a reusable subprocess boundary that can capture and correlate:

- command identity without leaking secret values;
- exit code;
- start/end/duration;
- stdout and stderr;
- PowerShell output when PowerShell is the child runtime;
- timeouts, launch failures and forced termination;
- child-process diagnostic files when integrations expose them.

Raw stdout/stderr must be retained in separate files when useful instead of stuffing unbounded terminal output into SQLite/events.

### End-of-run diagnostic report

At the end of an execution, generate automatically where a Diagnostics Session is enabled:

1. `report.md` — human-readable reconstruction;
2. `report.json` — machine-readable equivalent;
3. `diagnostics.jsonl` — ordered structured event stream;
4. referenced raw logs such as subprocess stdout/stderr;
5. `support-bundle.zip` — shareable package containing the above.

The report must summarize:

- execution identity, version/build/environment facts;
- start/end/duration and terminal status;
- workflows/nodes/stages executed;
- batches/items processed and counts where reported;
- decisions and branches selected;
- warnings/anomalies;
- errors/failures and traceback fingerprints;
- subprocess/PowerShell invocations and outcomes;
- results/artifacts/output summaries;
- Run Journal lifecycle when available;
- likely diagnostic hotspots/potential failure points based on recorded evidence, clearly marked as observations rather than guessed root causes.

### Privacy and safety

Diagnostics must be useful without becoming a secret dump.

- never snapshot the complete environment-variable set;
- redact recognized secret/token/password/cookie/header/query patterns;
- avoid arbitrary `repr()` of unknown runtime objects;
- allow values/fields to be explicitly marked sensitive;
- bound large payloads and point to files instead;
- support safe sharing as the default bundle mode.

### Quality / model diagnostics

The platform contract must support application-defined quality observations such as:

- confidence/score below threshold;
- missing/invalid expected outputs;
- inconsistent item counts;
- retry/fallback use;
- model/backend selected;
- degraded/partial result classification.

The diagnostics layer records these facts; domain Node Packs define what counts as low quality or inconsistent for their domain.

### Acceptance

M3 is resolved only when:

- core structured diagnostic events and redaction are tested;
- exception/traceback capture is tested;
- a subprocess smoke captures stdout + stderr + exit code;
- real `ktools-json` success and failure executions generate reports/bundles;
- CLI execution produces a diagnostic report automatically by default (with an explicit opt-out for tests/minimal consumers if needed);
- report/bundle survives process completion and is readable after restart;
- report content is deterministic enough for analysis but contains no known seeded secrets in security regression tests;
- hosted Windows/Linux CI passes.

This milestone establishes diagnostics/forensics. It does not claim automatic bug diagnosis or root-cause certainty.

---

## M4 — Artifact Lifecycle + Recovery + Semantic Cache

Status: **PLANNED — AFTER M3**

Build on M2 durable state and M3 diagnostics rather than inventing parallel state.

Targets:

- persistent Artifact provenance/validity records;
- stable node/input/config/version signatures;
- selective reuse of valid prior outputs;
- invalidation when inputs/config/node version/artifact validity changes;
- safe restart/recovery semantics and ownership rules;
- explicit `CACHED` / `RECOVERED` semantics only when evidence supports them;
- cleanup/retention policy for temporary/intermediate artifacts;
- diagnostic explanation of why a cache entry was reused or invalidated.

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

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

M4 adds:

- local file Artifact snapshots with size, mtime-ns and SHA-256;
- persistent Artifact occurrence/provenance via `SQLiteArtifactRegistry`;
- versioned nodes with `CachePolicy.NEVER` default and explicit `PURE` opt-in;
- stable semantic signatures over type/version/config/inputs/Artifact content;
- persistent fail-open `SQLiteNodeCache`;
- strong cached-output Artifact revalidation;
- explicit `NODE_CACHED` / `NodeRunStatus.CACHED` lifecycle truth;
- diagnostics for cache bypass/miss/hit/invalidation/store errors;
- core and JSON CLI `--cache` / `--artifact-registry` surfaces;
- real 2,000-record `json.split.plan` cache proof across SQLite close/reopen;
- proof that side-effectful `json.split` still republishes files on repeated runs;
- conservative restart recovery as new run + validated PURE reuse;
- no automatic old-RUNNING continuation or `RECOVERED` without ownership evidence;
- metadata-only retention with no automatic deletion of user outputs.

Accepted code candidate `c7ae2fa3953099d0bd9377da7c2c0195e96f6175` passed all five jobs in run `33560041360`.

The synchronized canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed all five jobs in run `33625955613`, satisfying the final promotion gate.

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

Carry-forward invariants:

- previous success is not sufficient for reuse;
- cacheability is explicit and capability-owned;
- side effects are never skipped without a proved replay/publication contract;
- cache/Artifact-registry failures remain supplemental where normal execution can proceed;
- `CACHED` is distinct from executed success;
- unfinished persisted state is not proof of process death;
- user output files are not automatically deleted from metadata invalidation;
- diagnostics is part of Definition of Done for significant native/subprocess/integration work.

## Active roadmap milestone — M5 Official local Node Packs

Status: **ACTIVE — DISCOVERY / SPEC GATE**.

Before changing implementation code, inspect actual legacy ownership and select the first small capability that is useful, deterministic enough to characterize, weakly coupled to the old monolith and capable of proving the M0-M4 platform contracts without duplicated business logic.

Current leading discovery candidate: legacy Markdown/TXT merge, because the stable monolith already contains a bounded `merge_text_files(...)` behavior with explicit input validation, separator modes, fallback decoding, output/input collision protection and atomic temporary-output replacement. This is not yet an implementation decision; it must be compared against other low-risk legacy capabilities before the M5 spec locks scope.

## Next exact action

Inventory low-risk legacy capabilities, compare coupling/dependencies/side effects/Artifact fit, select the first M5 slice, then create a dedicated spec and characterization tests before extraction.

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

Formal promotion commit `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` also passed its five-job matrix in run `33626260487`.

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

Typed file composition now includes:

- `FILE` for one file Artifact;
- `FILE_SET` for an ordered list/tuple of FILE Artifacts.

Carry-forward invariants:

- previous success is not sufficient for reuse;
- cacheability is explicit and capability-owned;
- side effects are never skipped without a proved replay/publication contract;
- cache/Artifact-registry failures remain supplemental where normal execution can proceed;
- `CACHED` is distinct from executed success;
- unfinished persisted state is not proof of process death;
- user output files are not automatically deleted from metadata invalidation;
- diagnostics is part of Definition of Done for significant native/subprocess/integration work;
- direct Tool/API and workflow routes share one capability owner rather than duplicate business logic.

## Active roadmap milestone — M5 Official local Node Packs

Status: **ACTIVE — ITERATIVE DELIVERY**.

### Slice 1 — Text Node Pack V1 — IMPLEMENTATION COMPLETE / PROMOTION GATE

Discovery compared Markdown/TXT merge, WebP→PNG and generic folder scanning. Markdown/TXT merge was selected because the stable monolith already contained a bounded stdlib-only `merge_text_files(...)` behavior with explicit input validation, separator modes, fallback decoding, output/input collision protection and atomic temporary-output replacement.

Implemented candidate:

- `DataType.FILE_SET` exact ordered collection contract;
- `files.literal` PURE local-file source whose cached Artifacts are strongly revalidated by M4;
- `packages/ktools-text/` as the canonical evolution owner;
- legacy-compatible Markdown/TXT decoding, separators and publication behavior;
- `text.merge.files: FILE_SET -> FILE`, cache policy NEVER because publication/replacement is required;
- first-class output Artifact provenance and ArtifactRegistry integration;
- source-file mutation invalidation for cached `files.literal` output;
- shared `ktools_core.local_files.path_from_file_uri()` after integration review found duplicated URI parsing;
- root CI Text package tests + real workflow smoke.

Accepted code candidate: `dbd39a1119ce1557d802a115404f01a3f797d93e`.

Hosted run `33627879876`: Ubuntu 3.10/3.13, Windows 3.10/3.13 and xyflow all succeeded. Representative Ubuntu/Python 3.10 evidence executed 72 core + 64 JSON + 15 Text tests plus core/JSON/Text smokes.

Ownership boundary: the old stable GUI still contains its historical merge implementation. That copy is now explicitly compatibility debt, not the canonical place to evolve semantics. New fixes/behavior originate in `ktools-text`; later traditional-Tool/UI migration must redirect or retire the historical copy.

## Next exact action

Require the synchronized canonical-memory HEAD of PR #8 to pass the same five-job hosted matrix. If green: mark PR #8 ready, revalidate exact head/base and unresolved review state, merge with expected-head guard, require post-merge `main` CI green, then continue M5 by re-inventorying real legacy owners for the next slice rather than preselecting one by convenience.

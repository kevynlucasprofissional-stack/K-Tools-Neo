# Current State — K-Tools Neo

## Current development truth

`main` is the integration truth. Active execution mode: **ChatGPT Solo Development Mode** under `docs/SOLO_DEVELOPMENT_MODE.md`. Canonical sequencing guide: `docs/ROADMAP.md`.

OpenCode, Antigravity and Codex remain paused as active writers unless the project owner explicitly re-enables them.

## Promoted platform milestones

### M0 — Platform Foundation — RESOLVED / PROMOTED
UI-independent `ktools-core`, typed node/port contracts, deterministic DAG validation/execution, initial Artifact model, CLI, Windows/Linux CI and bounded imported application subsystems.

### M1 — First official Node Pack — RESOLVED
`packages/ktools-json/` proves one capability owner shared by direct API and workflow use. Official JSON nodes include `json.literal` (PURE), `json.split.plan` (PURE) and `json.split` (NEVER).

### AG-001 — xyflow interaction spike — CLOSED
`spikes/xyflow-editor/` remains evidence that React + `@xyflow/react` is a credible interaction layer while `ktools-core` remains execution truth.

### M2 — Durable Execution V1 — RESOLVED
Optional Run Journal + stdlib SQLite persistence provide ordered run/node lifecycle history, query projections, error/output metadata, interruption reconciliation and `--journal` support.

### M3 — Diagnostics, Structured Logging + Support Bundle — RESOLVED / PROMOTED
Structured/share-safe diagnostics, exceptions/tracebacks, decisions/metrics/batches/anomalies, subprocess capture, PowerShell evidence, support reports/bundles, Ctrl+C classification and conservative abandoned-session packaging.

Final M3 closure checkpoint `5e1e46714aaefe0827c96a415d7d58d57790a187` passed run `33557338124`.

### M4 — Artifact Lifecycle + Recovery + Semantic Cache V1 — RESOLVED / PROMOTED
Strong local-file Artifact validity, persistent Artifact provenance, explicit cache policy, semantic signatures, persistent fail-open cache, cached-output revalidation, explicit CACHED lifecycle truth, cache diagnostics and conservative restart reuse.

Canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` passed run `33625955613`; formal promotion followed on `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` and its five-job matrix also succeeded.

## Runtime architecture now

```text
WorkflowEngine
  ├─ RunJournal          -> lifecycle truth/history
  ├─ DiagnosticsSession  -> forensic/support evidence
  ├─ NodeCache           -> validated reusable PURE results
  └─ ArtifactRegistry    -> Artifact occurrence/validity provenance

Typed values now include FILE and ordered FILE_SET for multi-file composition.
```

Carry-forward invariants:

- previous success is not sufficient for reuse;
- cacheability is explicit and capability-owned;
- side effects are never skipped without a proved replay/publication contract;
- `CACHED` is distinct from executed success;
- unfinished persisted state is not proof of process death;
- user output files are not automatically deleted from metadata invalidation;
- significant native/subprocess/integration work includes diagnostics;
- direct API/Tool and workflow routes share capability owners rather than duplicate business logic.

## M5 — Official local Node Packs — ACTIVE / ITERATIVE

### Slice 1 — Text Node Pack V1 — IMPLEMENTATION COMPLETE / PROMOTION GATE

Implemented candidate:

- `DataType.FILE_SET` exact ordered collection type;
- `files.literal` PURE ordered file source with M4 validity protection;
- `packages/ktools-text`;
- legacy-compatible Markdown/TXT merge behavior;
- `text.merge.files: FILE_SET -> FILE`, cache policy NEVER;
- first-class output Artifact provenance;
- shared local `file://` parser in core;
- root CI installation/tests + real Text workflow smoke.

Accepted code HEAD: `dbd39a1119ce1557d802a115404f01a3f797d93e`.

Hosted run `33627879876`: Ubuntu/Windows × Python 3.10/3.13 plus xyflow all succeeded.

Ownership decision: `packages/ktools-text` is the canonical evolution owner. The old stable GUI still contains a historical implementation and remains temporary compatibility debt until a later UI-adapter migration.

## Next exact action

Require the synchronized canonical-memory HEAD for PR #8 to pass the full five-job matrix. If green: mark PR #8 ready, revalidate its exact head/base, merge with expected-head guard, require post-merge `main` CI green, then continue M5 discovery for the next real local capability slice.

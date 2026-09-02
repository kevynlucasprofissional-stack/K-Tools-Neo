# Decisions — K-Tools Neo

## ADR-001 — K-Tools is a workflow platform, not a larger monolith

Status: ACCEPTED

The target architecture treats capabilities as reusable nodes/contracts. Ready-made tools become guided experiences or templates over those same capabilities.

Reason: this prevents duplicate implementations and allows simple usage, visual automation and future agent composition to share one operational language.

## ADR-002 — Workflow runtime is UI-independent

Status: ACCEPTED

The core engine must execute workflows without the desktop UI.

Reason: enables CLI tests, headless automation, deterministic validation and future alternative clients while keeping the visual editor replaceable.

## ADR-003 — Python is the first core runtime language

Status: ACCEPTED FOR CURRENT PLATFORM

The first `ktools-core` implementation is Python 3.10+.

Reason: most existing K-Tools utilities are Python, making capability extraction lower-risk. Node.js applications remain first-class through adapters/subprocess boundaries rather than forced rewrites.

Reopen if: profiling or integration evidence shows Python orchestration is a material bottleneck or the desktop host imposes a stronger runtime constraint.

## ADR-004 — Imported applications remain bounded subsystems

Status: ACCEPTED

`xcursos-runner` and `yt-dlp-tui` keep their native internals. K-Tools integrates them through explicit adapters/nodes first.

Reason: preserves mature retry, diagnostics, auth and download behavior already implemented in those projects.

## ADR-005 — Typed ports and Artifact provenance are core concepts

Status: ACCEPTED

Connections are validated by declared data types before execution. File-like results evolve toward `Artifact` objects that preserve identity/provenance instead of only passing naked filesystem strings.

## ADR-006 — xyflow is the preferred visual-canvas implementation, not the workflow engine

Status: **SPIKE-VALIDATED / PRODUCTION-CONTRACT GATED**

`@xyflow/react` remains the preferred graph interaction layer.

Reason: source research and the audited `spikes/xyflow-editor/` implementation proved that xyflow can own viewport, node/edge interaction, handles, controlled graph state, palette/canvas/inspector composition and typed-connection preflight without requiring it to own K-Tools execution semantics.

Boundary: `ktools-core` remains the authority for workflow semantics, type validation, persistence and execution. The frontend may provide immediate feedback but must consume/revalidate shared runtime contracts.

The spike did **not** yet prove production large-graph performance, lossless MissingNode serialization round-trip, complete reconnection behavior, accessibility compliance or the desktop host.

Reopen if: the later production-editor contract exposes material performance, packaging or customization constraints that xyflow cannot satisfy.

## ADR-007 — Node Packs are the extension boundary; workflows may become reusable nodes/tools

Status: ACCEPTED AS PRODUCT ARCHITECTURE

New capability families should converge on versioned Node Packs rather than registration logic scattered across the engine or UI.

A future saved workflow may expose typed public inputs/outputs and become a reusable workflow-node. The same workflow may also be projected as a simplified ready-made Tool through presets/forms, without a second business-logic implementation.

Reason: Node-RED's registry/subflow model, Activepieces Pieces, ComfyUI custom-node loading and n8n's implementation-free synthetic tool pattern independently support this boundary. This also preserves ADR-001's one-capability/one-owner invariant.

Implementation rule: start with official/static Node Packs and only add dynamic/community plugin installation after there is an explicit compatibility and security model.

## ADR-008 — Direct invocation and workflow nodes share one capability owner

Status: **PROVED / ACCEPTED**

A reusable capability must not have separate business-logic implementations for direct Tool/API use and workflow use.

The first production proof is `packages/ktools-json/`:

```text
Direct API (`ktools_json.api.split_json`)
                 \
                  -> `writer.split_and_write`
                         -> `capability.split_json_document`
                  /
Workflow node (`json.split`)
```

The direct and workflow routes share transformation/file-publication owners and produce byte-identical part files under equivalent input/config in integration tests.

Reason: this pattern is the mechanism that allows traditional simple tools, workflows and future agent composition to remain one product instead of three implementations drifting apart.

Implementation rule: future Node Packs should preserve the same shape. UI components and workflow adapters are callers/adapters, not capability owners.

## ADR-009 — Durable execution precedes production editor and broad expensive-workflow rollout

Status: **PROVED AS SEQUENCING DECISION**

After proving a real Node Pack, the next platform boundary is Run Journal + durable run/node persistence before production editor work and before expensive media pipelines become first-class workflows.

Reason:

- the editor needs real run/node event contracts rather than simulated frontend state;
- expensive media work needs observable interruption/failure history before resume/cache can be trusted;
- Artifact provenance requires a durable run/node identity boundary;
- recovery/cache should build on recorded execution state rather than create a second parallel state model.

M2 implemented and hosted-tested this boundary.

## ADR-010 — RunJournal is the runtime contract; SQLite is a persistence implementation

Status: **PROVED / ACCEPTED FOR DURABLE EXECUTION V1**

`WorkflowEngine` depends on an injected `RunJournal` contract rather than directly depending on SQLite.

Accepted shape:

```text
WorkflowEngine
      ↓
  RunJournal
   ↙      ↘
Memory    SQLite
```

Consequences:

- `WorkflowEngine(registry)` remains a valid storage-free execution path;
- `MemoryRunJournal` supports deterministic/ephemeral observation;
- `SQLiteRunJournal` provides durable history/query projections without making a database mandatory for every consumer;
- future UI/transports may consume the same logical event model without redefining engine state.

## ADR-011 — Ordered events are execution history; run/node tables are V1 query projections

Status: **ACCEPTED FOR V1**

Durable events preserve the logical ordered history. `runs` and `node_runs` are query-friendly projections updated in the same SQLite transaction as each event.

This is deliberately **not** a claim of full event sourcing.

## ADR-012 — Interrupted execution is distinct from Failed and reconciliation is explicit in V1

Status: **PROVED / ACCEPTED**

A run left `RUNNING` because a process/session disappeared is not a normal business/runtime `FAILED` result.

`SQLiteRunJournal.reconcile_incomplete_runs()` explicitly projects unfinished run/node records to `INTERRUPTED` using journal events.

It does **not** execute automatically when a database is opened because another live process may still legitimately own a `RUNNING` record. Automatic recovery requires a future process/session ownership or lease model.

## ADR-013 — Durable output metadata uses an explicit serialization allow-list

Status: **PROVED / ACCEPTED**

Journal serialization explicitly supports JSON-like structures and approved K-Tools runtime types such as `Artifact`, paths, enums and dates. Unknown custom Python objects degrade to qualified type-only metadata and are marked non-serializable.

Do not persist arbitrary `repr()`, dataclass internals, object attributes or generic custom `to_dict()` results merely for observability.

## ADR-014 — Diagnostics is a first-class cross-cutting platform contract

Status: **ACCEPTED / IMPLEMENTED FOR V1**

Diagnostics must be built before broad cache/recovery, media, browser and imported-app integration work rather than retrofitted after failures become complex.

`WorkflowEngine` therefore accepts an optional `DiagnosticsSession` independently of `RunJournal`.

```text
                WorkflowEngine
                 ↙          ↘
        RunJournal       DiagnosticsSession
     lifecycle truth     forensic/support evidence
```

Run Journal owns durable execution-state facts. Diagnostics owns richer support evidence and must not mutate/redefine journal state.

## ADR-015 — Share-safe diagnostics are the default; diagnostic reports do not claim root cause

Status: **ACCEPTED / SECURITY AND SUPPORT INVARIANT**

Required default behavior includes recognized credential redaction, no wholesale environment snapshot, no arbitrary unknown-object repr/reflection, bounded structured strings, redacted child-process output and concise operational decisions without private chain-of-thought.

`diagnosticHotspots` summarizes recorded facts; it is not automatic causal diagnosis.

## ADR-016 — Abnormal diagnostic-session recovery requires staleness evidence

Status: **ACCEPTED FOR V1**

A diagnostics directory with an event stream but no final report can result from abnormal termination, but absence of a report alone does not prove that the owner process is dead.

`recover_abandoned_sessions()` therefore requires staleness unless the caller independently knows no live process owns the session.

## ADR-017 — Semantic cache is explicit opt-in and fail-open

Status: **PROVED / ACCEPTED FOR M4 V1**

Every node defaults to `CachePolicy.NEVER`. Only a capability owner may explicitly mark a versioned node `PURE` when equivalent semantic inputs/config produce deterministic outputs and skipping the handler has no required external side effect.

`NodeCache` is an optional injected optimization. Cache failures fall back to normal execution where possible.

## ADR-018 — Cached execution is a distinct lifecycle fact

Status: **PROVED / ACCEPTED**

If a handler is skipped because a prior output is substituted, the journal records `NODE_CACHED` and projects `NodeRunStatus.CACHED`.

A cached node does not emit `NODE_STARTED` and is not rewritten as ordinary executed success.

## ADR-019 — Strong reusable file validity requires content identity

Status: **PROVED / ACCEPTED FOR LOCAL FILE V1**

For reusable local file Artifacts, size and mtime are quick invalidation evidence but are not sufficient to claim equality. If quick fields still match, K-Tools recomputes SHA-256 before reuse.

Folders and remote URIs remain without strong V1 validity until dedicated contracts exist.

`SQLiteArtifactRegistry` preserves per-run/node/output occurrence provenance and historical snapshots without deleting user files.

## ADR-020 — Restart recovery is a new run until ownership is proved

Status: **ACCEPTED SAFETY BOUNDARY**

M4 recovery means starting a new run and selectively substituting validated completed PURE results through semantic cache.

It does not mean taking an old `RUNNING` row and continuing it automatically. `RECOVERED` remains unavailable until a later process/session ownership contract proves atomic acquisition, liveness/takeover and side-effect replay/idempotency.

Retention rule: M4 cache/Artifact-registry stores own metadata only. K-Tools does not automatically delete user output Artifacts.

## ADR-021 — FILE_SET is an ordered exact collection contract in V1

Status: **PROVED / ACCEPTED IN M5 TEXT SLICE**

`DataType.FILE_SET` represents an ordered list/tuple of FILE Artifacts for workflow composition.

V1 static compatibility is exact FILE_SET→FILE_SET. FILE and FILE_SET are not interchangeable, and collections are not smuggled through JSON/ANY merely for convenience.

No dedicated collection class is introduced because M4 semantic-signature and Artifact traversal already handle list/tuple containers recursively while preserving list order.

`files.literal` is the minimal built-in local source for this contract. It is `PURE`: it publishes no external side effect, and M4 strong Artifact revalidation prevents a cached FILE_SET from silently surviving missing/changed source files.

Reopen covariance or richer collection semantics only when a real capability requires them.

## ADR-022 — Text merge publication remains NEVER; ktools-text is the canonical owner

Status: **PROVED / ACCEPTED FOR TEXT NODE PACK V1**

`text.merge.files` is `NEVER` even though its formatting is deterministic.

Reason: the node's required behavior includes publishing/replacing the configured destination. Returning a cached Artifact reference would not perform that required side effect.

Canonical evolution owner for Markdown/TXT merge behavior is `packages/ktools-text/src/ktools_text/`. Direct API and workflow adapter both delegate to `writer.merge_text_files`, and byte-equivalence tests prove they do not own separate merge algorithms.

The stable legacy GUI still contains a historical implementation. It is explicitly compatibility debt, not a second canonical owner. New semantics and bug fixes must originate in `ktools-text`; a later traditional-Tool/UI migration must redirect or retire the historical copy.

This permits incremental migration without pretending a full GUI rewrite occurred in this slice.

## ADR-023 — Local file URI interpretation belongs to ktools-core

Status: **PROVED / ACCEPTED**

M5 integration review found duplicate `file:// URI → Path` parsing in M4 cache identity and the Text adapter despite green behavior tests.

`ktools_core.local_files.path_from_file_uri()` now owns the cross-platform V1 policy: ordinary local file URIs and `localhost` are accepted; remote/UNC authorities are rejected.

Capability-specific layers translate the generic `LocalFileUriError` into their own public error taxonomy.

Reason: local file identity/URI interpretation is a platform boundary shared by Artifact validity and file-based Node Packs, not business logic each pack should independently reimplement.

## Research and audit records

Source-based workflow-platform comparative study: `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`.

Audited xyflow spike: `docs/multi-agent/handoffs/AG-001-AUDIT.md`.

Audited first official Node Pack: `docs/multi-agent/handoffs/OC-001-AUDIT.md`.

Durable Execution V1 evidence: `docs/specs/durable-execution-v1/evidence.md`.

Diagnostics + Support Bundle V1 evidence: `docs/specs/diagnostics-support-bundle-v1/evidence.md`.

Artifact Lifecycle + Recovery + Semantic Cache V1 evidence: `docs/specs/artifact-recovery-cache-v1/evidence.md`.

Text Node Pack V1 evidence: `docs/specs/text-node-pack-v1/evidence.md`.

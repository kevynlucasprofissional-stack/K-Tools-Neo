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

M2 implemented and hosted-tested this boundary. Full resume and semantic cache remain later milestones.

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

Evidence: M2 hosted runs recorded in `docs/specs/durable-execution-v1/evidence.md`.

## ADR-011 — Ordered events are execution history; run/node tables are V1 query projections

Status: **ACCEPTED FOR V1**

Durable events preserve the logical ordered history. `runs` and `node_runs` are query-friendly projections updated in the same SQLite transaction as each event.

This is deliberately **not** a claim of full event sourcing. K-Tools does not yet promise replay-to-rebuild, schema-event migrations or distributed event consumers.

Reason: this gives future UI/history/recovery logic stable ordered facts while keeping common history queries simple.

Implementation rule: M3 cache/artifact/recovery state must extend these run/node identities rather than introduce a disconnected execution-history model.

## ADR-012 — Interrupted execution is distinct from Failed and reconciliation is explicit in V1

Status: **PROVED / ACCEPTED**

A run left `RUNNING` because a process/session disappeared is not a normal business/runtime `FAILED` result.

`SQLiteRunJournal.reconcile_incomplete_runs()` explicitly projects unfinished run/node records to `INTERRUPTED` using journal events.

It does **not** execute automatically when a database is opened because another live process may still legitimately own a `RUNNING` record. Automatic recovery requires a future process/session ownership or lease model.

Implementation rule: do not implement automatic resume by treating every old `RUNNING` record as abandoned.

## ADR-013 — Durable output metadata uses an explicit serialization allow-list

Status: **PROVED / ACCEPTED**

Journal serialization explicitly supports JSON-like structures and approved K-Tools runtime types such as `Artifact`, paths, enums and dates. Unknown custom Python objects degrade to qualified type-only metadata and are marked non-serializable.

Do not persist arbitrary `repr()`, dataclass internals, object attributes or generic custom `to_dict()` results merely for observability.

Reason: runtime observability should not unexpectedly reflect opaque object internals/secrets into durable local history, and persistence must remain deterministic enough for later cache/signature work.

## Research and audit records

Source-based workflow-platform comparative study:

`docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`

Audited xyflow spike:

`docs/multi-agent/handoffs/AG-001-AUDIT.md`

Audited first official Node Pack:

`docs/multi-agent/handoffs/OC-001-AUDIT.md`

Durable Execution V1 evidence:

`docs/specs/durable-execution-v1/evidence.md`

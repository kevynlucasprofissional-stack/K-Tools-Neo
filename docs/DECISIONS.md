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

## ADR-009 — Durable execution is the next platform boundary before production editor or broad media migration

Status: ACCEPTED AS SEQUENCING DECISION

After proving a real Node Pack, the next platform milestone is Run Journal + durable run/node persistence before broad production editor work and before expensive media pipelines become first-class workflows.

Reason:

- the editor needs real run/node event contracts rather than simulated frontend state;
- expensive media work needs observable interruption/failure history before resume/cache can be trusted;
- Artifact provenance requires a durable run/node identity boundary;
- recovery/cache should build on recorded execution state rather than create a second parallel state model.

Scope rule: Durable Execution V1 establishes journal/persistence/history first. Full resume and semantic cache remain later milestones unless implementation evidence shows a safe trivial extension.

## Research and audit records

Source-based workflow-platform comparative study:

`docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`

Audited xyflow spike:

`docs/multi-agent/handoffs/AG-001-AUDIT.md`

Audited first official Node Pack:

`docs/multi-agent/handoffs/OC-001-AUDIT.md`

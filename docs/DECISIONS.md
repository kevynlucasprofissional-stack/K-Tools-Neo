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

Status: ACCEPTED FOR FOUNDATION

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

Status: RESEARCH-VALIDATED / IMPLEMENTATION-GATED

The first real visual-editor spike should use `@xyflow/react` as the canvas interaction layer.

Reason: source review confirmed that xyflow cleanly owns viewport, node/edge interaction, handles, connection validation hooks and graph-view utilities without requiring it to own K-Tools execution semantics. The studied Activepieces source also uses `@xyflow/react` throughout its production-oriented workflow builder, reducing adoption risk for this product class. The snapshot is MIT-licensed.

Boundary: `ktools-core` remains the authority for workflow semantics, type validation, persistence and execution. The frontend may provide immediate connection feedback but must revalidate through core contracts.

Still open: the desktop host (for example Tauri/Electron), packaging, native bridge and K-Tools-specific performance must be proven by a dedicated UI/desktop spike before the visual editor is promoted as delivered product architecture.

Reopen if: the spike demonstrates material performance, packaging or customization constraints that xyflow cannot satisfy.

## ADR-007 — Node Packs are the extension boundary; workflows may become reusable nodes/tools

Status: ACCEPTED AS PRODUCT ARCHITECTURE

New capability families should converge on versioned Node Packs rather than registration logic scattered across the engine or UI.

A future saved workflow may expose typed public inputs/outputs and become a reusable workflow-node. The same workflow may also be projected as a simplified ready-made Tool through presets/forms, without a second business-logic implementation.

Reason: Node-RED's registry/subflow model, Activepieces Pieces, ComfyUI custom-node loading and n8n's implementation-free synthetic tool pattern independently support this boundary. This also preserves ADR-001's one-capability/one-owner invariant.

Implementation rule: start with official/static Node Packs and only add dynamic/community plugin installation after there is an explicit compatibility and security model.

## Research record

The source-based comparative study that supports ADR-006/ADR-007 is versioned at:

`docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`

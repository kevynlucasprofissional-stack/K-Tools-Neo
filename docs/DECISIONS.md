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

## ADR-006 — Visual editor library is not yet a core dependency

Status: DEFERRED

React Flow is the leading candidate for the future canvas, informed by prior research, but the choice is intentionally outside the foundation implementation. A dedicated UI spike must validate packaging, desktop host, performance, node customization and licensing before promotion to a stable architectural dependency.

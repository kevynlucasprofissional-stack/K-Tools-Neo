# Current State — K-Tools Neo

Foundation promotion checkpoint: `bf6b5282a3df033a1394b05215a1ed97492a73c1`
Foundation PR: #1 — `feat(platform): establish typed workflow foundation`
Foundation final candidate head: `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7`

## Current production state

The first K-Tools Neo platform foundation is **PROMOTED TO `main`**.

Working now:

- `packages/ktools-core/` provides a UI-independent workflow runtime;
- typed node/port contracts exist;
- graph validation rejects unknown nodes/ports, duplicate target-input connections, missing required inputs, incompatible types and cycles;
- deterministic DAG execution exists;
- initial `Artifact` model exists with identity/provenance fields and JSON round-trip;
- headless JSON workflow CLI exists;
- root CI validates Ubuntu/Windows × Python 3.10/3.13;
- root `.gitignore` covers Python/Node build output and common local secret/runtime files;
- canonical engineering memory exists under `docs/`;
- workflow-platform source research exists at `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`;
- multi-agent operating model exists at `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md`;
- concrete OpenCode/Antigravity next-wave packets exist at `docs/multi-agent/NEXT_WAVE_ASSIGNMENTS.md` after this post-merge closure is promoted.

## Foundation evidence

Local evidence:

- 10 unit/contract tests PASS;
- CLI smoke PASS, producing `K-Tools Neo`.

Hosted acceptance after the repository became public:

- run `33330660076` on SHA `1ccffb11af25a8d993ead931183380d354746131`: success;
- final exact-head run `33330801547` on SHA `91fe5cfb45fe7ef44dd7e564238a4ce77ed84bf7`: success.

Final matrix evidence:

- Ubuntu / Python 3.10: success;
- Ubuntu / Python 3.13: success;
- Windows / Python 3.10: success;
- Windows / Python 3.13: success;
- Checkout, Setup Python, editable install, unit/contract tests and CLI smoke all passed.

Historical red Actions runs were proved to be an external account payment/spending-limit job-start condition, not a K-Tools product failure.

## Existing product/subsystems preserved

- `K Tools Neo - Versão Estável 2.py` remains the legacy integrated GUI/current behavior inventory;
- loose Python utilities remain available for incremental migration;
- `apps/xcursos-runner/` remains an imported Node.js subsystem;
- `apps/yt-dlp-tui/` remains an imported Python subsystem;
- imported app internals were not rewritten by the Foundation.

## Not implemented yet

- first real K-Tools capability/Node Pack proof;
- workflow/run/artifact persistence and Run Journal;
- restart/recovery and semantic cache;
- production visual workflow editor;
- desktop-host selection/validation;
- adapters for XCursos Runner or YT-DLP TUI;
- workflow templates replacing legacy tool screens;
- agent/natural-language workflow generation.

## Architecture direction now accepted

- one capability / one implementation owner;
- direct Tool usage and Workflow usage share capability implementations;
- `ktools-core` remains workflow/runtime authority;
- `@xyflow/react` is the preferred first canvas dependency for a dedicated UI spike;
- Run Journal + Artifact persistence should precede broad production use of expensive media workflows;
- third-party source reuse must be classified by licensing and ownership boundary before copying code.

## Multi-agent operating state

ChatGPT: Conductor / Chief Architect / Integration Engineer.

OpenCode: Runtime / Backend Implementation Lead.

Antigravity: Frontend / UX / Product Prototype Lead.

Codex: intentionally excluded from the K-Tools agent pool for now.

Immediate parallel wave after this post-merge memory closure:

1. OpenCode — OC-001: first real capability / Node Pack proof;
2. Antigravity — AG-001: isolated xyflow editor interaction spike using fixtures;
3. ChatGPT — C-001: active spec, contract arbitration, review and integration.

OpenCode and Antigravity must work in isolated branches/worktrees with disjoint ownership. Neither merges directly to `main`.

## Next production milestone

Create a new spec whose core acceptance claim is:

> one existing useful K-Tools capability has one implementation owner and is demonstrably reusable through both a direct path and a workflow node.

The first capability choice must come from repository evidence and candidate ranking, not convenience alone. The validated result then informs the Run Journal / persistence milestone and the later production editor contract.

## Foundation terminal state

**RESOLVED / PROMOTED.**

The Foundation spec is closed. Future work must not keep extending the Foundation spec as a catch-all; use new specs for new product milestones.

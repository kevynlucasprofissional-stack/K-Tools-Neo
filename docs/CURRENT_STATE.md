# Current State — K-Tools Neo

Platform-foundation cycle based on `main` at `e6fb80f78f4e4e4f943ea6567320161407fe7b5f`.

## Main baseline at start

- Default branch: `main`.
- Baseline head: `e6fb80f78f4e4e4f943ea6567320161407fe7b5f`.
- No open pull requests were present at discovery time.
- Only `main` existed as a branch at discovery time.
- `main` was not protected and had no required status checks.
- No root `.github/workflows/` directory existed.
- No canonical K-Tools `AGENTS.md`, constitution, current-state, decisions, testing policy or Engineering Journal existed.

## Working now in PR #1 candidate

The PR branch contains the first platform foundation plus the workflow-platform source study and the multi-agent development protocol.

- `packages/ktools-core/` provides the first UI-independent workflow runtime.
- Typed node/port contracts exist.
- Graph validation rejects unknown nodes/ports, duplicate target-input connections, missing required inputs, incompatible types and cycles.
- Deterministic DAG execution exists.
- Initial `Artifact` model exists with provenance fields and JSON round-trip.
- CLI execution exists for JSON workflow definitions.
- Root CI exists for Ubuntu/Windows and Python 3.10/3.13 with read-only repository contents permission.
- Root `.gitignore` covers Python/Node build output and common local secret/runtime files.
- Canonical engineering memory exists under `docs/`.
- Local evidence: 10 unit/contract tests PASS and CLI smoke PASS.
- `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md` records the supplied-source study and reuse/licensing boundaries.
- `docs/multi-agent/MULTI_AGENT_DEVELOPMENT_PLAN.md` defines ChatGPT as Conductor, OpenCode as Runtime/Backend lead and Antigravity as Frontend/UX lead; Codex is explicitly excluded from this project's agent pool for now.

## CI boundary status

Historical Actions runs:

- run `33327645359` on `3fb12310f531a3754c751116fdc5470ab29ea159`;
- run `33327842478` on `4fdf578aee02051625462df85f1058d6882490d1` after matrix/permission hardening.

Both failed before any step was exposed by the GitHub API. The later GitHub UI annotation proved the platform root cause: the jobs were not started because recent account payments had failed or the spending limit needed to be increased.

Classification: **historical failures were external GitHub Actions account/billing job-start failures, not K-Tools product failures**.

Material environment change now confirmed:

- repository changed from private to public;
- GitHub repository metadata reports `visibility: public`.

A new exact-current-head PR run is therefore justified and is the next acceptance evidence. It must actually reach Checkout, Setup Python, editable install, unit/contract tests and CLI smoke on Windows + Ubuntu.

## Existing product/subsystems preserved

- `K Tools Neo - Versão Estável 2.py` remains the current legacy integrated GUI.
- Loose Python utilities remain untouched.
- `apps/xcursos-runner/` remains an imported Node.js subsystem.
- `apps/yt-dlp-tui/` remains an imported Python subsystem.

## Not implemented yet

- Production visual workflow editor.
- Persistence of workflows/runs/artifacts.
- Real filesystem/media/PDF node packs.
- Adapters for XCursos Runner or YT-DLP TUI.
- Workflow templates replacing legacy tool screens.
- Agent/natural-language workflow generation.

## Promotion status

**RETESTING — do not merge PR #1 until the new exact-head CI is green.**

If the new jobs reach the product and fail, fix the first evidenced product/workflow boundary and retest. If Windows + Ubuntu are green, synchronize final evidence/memory, run the exact-head audit, rerun CI on that final memory-closure head, and promote only after that final run is green.

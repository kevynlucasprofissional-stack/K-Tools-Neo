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

Candidate code/CI ref validated locally and exercised by Actions: `4fdf578aee02051625462df85f1058d6882490d1`.

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

## CI boundary status

Two materially distinct GitHub Actions attempts reached the same failure boundary:

- run `33327645359` on `3fb12310f531a3754c751116fdc5470ab29ea159`;
- run `33327842478` on `4fdf578aee02051625462df85f1058d6882490d1` after matrix/permission hardening.

In both cases all matrix jobs concluded `failure` before any step was exposed by the GitHub API; log retrieval returned `BlobNotFound`. There is no evidence that checkout, Python setup, package install, tests or the K-Tools CLI executed.

Classification: **external GitHub Actions / runner job-start boundary; exact cause unknown from the connected API**.

## Existing product/subsystems preserved

- `K Tools Neo - Versão Estável 2.py` remains the current legacy integrated GUI.
- Loose Python utilities remain untouched.
- `apps/xcursos-runner/` remains an imported Node.js subsystem.
- `apps/yt-dlp-tui/` remains an imported Python subsystem.

## Not implemented yet

- Visual workflow editor.
- Persistence of workflows/runs/artifacts.
- Real filesystem/media/PDF nodes.
- Adapters for XCursos Runner or YT-DLP TUI.
- Workflow templates replacing legacy tool screens.
- Agent/natural-language workflow generation.

## Promotion status

**BLOCKED — do not merge PR #1 yet.**

The code candidate is locally validated and the integration diff is reviewable, but `AC-007.1` requires successful exact-candidate CI on Windows and Ubuntu. Promotion resumes after GitHub Actions can start a job and run the workflow steps.

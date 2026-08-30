# Current State — K-Tools Neo

Last synchronized for the platform-foundation candidate created from `main` at `e6fb80f78f4e4e4f943ea6567320161407fe7b5f`.

## Main baseline at start

- Default branch: `main`.
- `main` head: `e6fb80f78f4e4e4f943ea6567320161407fe7b5f`.
- No open pull requests were present at discovery time.
- Only `main` existed as a branch at discovery time.
- `main` was not protected and had no required status checks.
- No root `.github/workflows/` directory existed.
- No canonical K-Tools `AGENTS.md`, constitution, current-state, decisions, testing policy or Engineering Journal existed.

## Working now in the candidate branch

- `packages/ktools-core/` provides the first UI-independent workflow runtime.
- Typed node/port contracts exist.
- Graph validation rejects unknown nodes/ports, duplicate input connections, missing required inputs, incompatible types and cycles.
- Deterministic DAG execution exists.
- Initial `Artifact` model exists with provenance fields and JSON round-trip.
- CLI execution exists for JSON workflow definitions.
- Root CI is introduced for Ubuntu/Windows and Python 3.11/3.13.
- Canonical engineering memory is introduced under `docs/`.

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

Candidate implementation is isolated on `feat/platform-foundation-workflow-engine`; promotion to `main` requires exact-branch CI and integration review.

# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. GitHub Actions discovers workflows from the repository root `.github/workflows`, so these imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications after the core foundation lands.

## KI-002 — Legacy GUI owns large amounts of business logic

Status: OPEN

`K Tools Neo - Versão Estável 2.py` is a large monolithic GUI/application file. Capability logic is not yet cleanly separable from presentation.

Next: inventory functions and extract the first low-risk capability pack behind node contracts.

## KI-003 — No real K-Tools utility node is integrated yet

Status: OPEN

Foundation nodes are intentionally deterministic fixtures (`text.literal`, `text.concat`, etc.). They prove graph contracts, not product utility coverage.

## KI-004 — Workflow/run/artifact persistence is absent

Status: OPEN

The first engine runs in memory. Restart/recovery, cache and artifact lifecycle are not implemented.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No canvas/palette/inspector/run UI exists yet.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

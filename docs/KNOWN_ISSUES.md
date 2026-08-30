# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

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

## KI-007 — GitHub Actions jobs fail before first recorded step

Status: BLOCKING / EXTERNAL BOUNDARY

Two materially distinct root-CI attempts created the expected Windows/Ubuntu matrices but every job failed before a checkout/setup/install/test step was exposed. A representative job returns an empty step list and its log endpoint returns `BlobNotFound`.

Impact: the exact-candidate Windows/Ubuntu acceptance criterion cannot currently be proven, so PR #1 must not be promoted.

What is known:

- the workflow file is discovered;
- matrix jobs are created;
- the failure occurs before a product step is observable.

What is not known from the connected API:

- the account/repository/runner-side reason GitHub refuses or fails to start the job.

Resolution condition: GitHub Actions starts the jobs and the workflow reaches checkout/install/test/CLI steps; then fix any product/workflow failures evidenced at those boundaries and obtain green exact-candidate CI.

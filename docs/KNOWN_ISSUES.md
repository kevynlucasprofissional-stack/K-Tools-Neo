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

The workflow-platform source study strengthens the priority of a Run Journal + Artifact persistence before expensive media workflows become a primary visual-editor path. See `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No canvas/palette/inspector/run UI exists yet.

Research now identifies `@xyflow/react` as the preferred implementation for the first UI spike, while `ktools-core` remains the workflow/runtime authority. Desktop-host integration and target-environment performance remain unproved.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

## KI-007 — Historical GitHub Actions jobs were blocked by billing/spending state

Status: ROOT CAUSE IDENTIFIED / RETESTING

Two root-CI attempts created the expected Windows/Ubuntu matrices but every job failed before checkout/setup/install/test.

The GitHub Actions UI subsequently exposed the missing platform reason: the jobs were not started because recent account payments had failed or the spending limit needed to be increased. This classifies the historical failures as an external account/billing Actions boundary rather than a K-Tools product failure.

Material environment change:

- the repository was changed from private to public;
- the GitHub repository API now reports `visibility: public`.

Impact now: historical red runs remain invalid evidence for Windows/Linux product behavior. A new exact-head run is required to prove the environment change actually allows hosted jobs to start.

Resolution condition:

1. a new PR run reaches Checkout/Setup Python/Install;
2. Windows + Ubuntu unit/contract + CLI smoke complete successfully;
3. evidence/current-state/tasks are synchronized;
4. only then may PR #1 be promoted.

If the platform still reports the same billing annotation, remain externally blocked and do not modify product code as a workaround.

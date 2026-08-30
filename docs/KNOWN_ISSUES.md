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

Status: RESOLVED

Historical symptom:

- runs `33327645359` and `33327842478` created the matrix but failed before checkout/setup/install/test;
- the GitHub UI later exposed the reason: recent account payments had failed or the spending limit needed to be increased.

Classification: external GitHub Actions account/billing job-start failure; not a K-Tools product failure.

Material environment change:

- repository changed from private to public;
- GitHub repository API confirmed `visibility: public`.

Resolution evidence:

- exact-head run `33330660076` on `1ccffb11af25a8d993ead931183380d354746131` completed successfully;
- Ubuntu 3.10: success;
- Ubuntu 3.13: success;
- Windows 3.10: success;
- Windows 3.13: success;
- each matrix path reached Checkout, Setup Python, editable install, unit/contract tests and CLI smoke successfully.

Result: the historical job-start blocker is closed. Future CI failures must be classified from their actual first failing step rather than carried forward from the billing incident.

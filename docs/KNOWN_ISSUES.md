# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications after the core foundation lands / before imported-app adapters are promoted.

## KI-002 — Legacy GUI owns large amounts of business logic

Status: OPEN / REDUCED BY M5 SLICE 1

`K Tools Neo - Versão Estável 2.py` is a large monolithic GUI/application file. Capability logic is not yet cleanly separable from presentation across the whole application.

M5 Text Node Pack V1 extracts the canonical Markdown/TXT merge capability and proves a migration pattern, but many other utilities remain embedded in the monolith.

Next: continue capability-by-capability extraction behind node contracts rather than broad monolith rewrite.

## KI-003 — No real K-Tools utility node is integrated yet

Status: RESOLVED

Historical foundation condition. `packages/ktools-json/` is the first official real Node Pack, and M5 Slice 1 adds `text.merge.files` plus the `files.literal` ordered-file source contract.

## KI-004 — Workflow/run/artifact persistence is absent

Status: RESOLVED

Historical foundation condition. M2 implements durable run/node history with RunJournal + SQLite. M4 implements persistent Artifact occurrence/validity observations and semantic cache.

Automatic continuation of old in-flight RUNNING work remains deliberately ownership-gated; this is a recovery-safety boundary, not absence of persistence.

The workflow-platform source study remains relevant sequencing evidence. See `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No production canvas/palette/inspector/run UI exists yet.

Research and the audited spike identify `@xyflow/react` as the preferred implementation layer, while `ktools-core` remains the workflow/runtime authority. Desktop-host integration and target-environment performance remain unproved.

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

## KI-008 — Legacy stable GUI is not yet wired to canonical Text Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-text` is the canonical evolution owner for Markdown/TXT merge, but `K Tools Neo - Versão Estável 2.py` still executes its historical implementation.

Impact: the old GUI can drift if someone changes the historical copy directly.

Invariant until migration: new behavior/bug fixes must originate in `ktools-text`; the historical copy is frozen as an old compatibility path.

Next: when the traditional Tool surface is migrated to the platform runtime, redirect the GUI/tool path to `ktools-text` and remove or reduce the historical duplicate. Do not disguise this debt, but do not block Text Node Pack V1 on a full GUI rewrite.

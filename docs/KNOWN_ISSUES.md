# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications before their adapter milestone is promoted.

## KI-002 — Legacy GUI still contains large amounts of business logic

Status: OPEN / REDUCED BY M5 SLICE 1

`K Tools Neo - Versão Estável 2.py` remains a large monolithic GUI/application file.

M5 Text Node Pack V1 extracts the canonical Markdown/TXT merge capability, proving the migration pattern, but many other utilities are still embedded in the monolith.

Next: continue capability-by-capability extraction under explicit specs rather than broad monolith rewrite.

## KI-003 — No real K-Tools utility node integrated

Status: RESOLVED

Historical foundation-only condition. `packages/ktools-json` is the first official real Node Pack and M5 adds `text.merge.files` plus `files.literal` composition support.

## KI-004 — Workflow/run/artifact persistence absent

Status: RESOLVED

Historical condition. M2 provides durable Run Journal/SQLite execution history; M4 provides persistent Artifact registry, semantic cache and strong local-file validity.

Automatic continuation of old in-flight RUNNING work remains deliberately ownership-gated, but persistence itself is implemented.

## KI-005 — Production visual workflow editor is absent

Status: OPEN

The audited xyflow spike exists and remains green, but no production canvas/palette/inspector/run UI exists yet.

`@xyflow/react` is the preferred interaction layer subject to the later Runtime Contract API and production-editor gate.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

## KI-007 — Historical GitHub Actions jobs were blocked by billing/spending state

Status: RESOLVED

Historical runs failed before product steps because of the account/spending state. After the material environment change, exact-head hosted jobs reached product boundaries and succeeded. Future CI failures are classified from their actual first failing step rather than carrying forward this incident.

## KI-008 — Legacy stable GUI is not yet wired to canonical Text Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-text` is the canonical owner for Markdown/TXT merge evolution, but `K Tools Neo - Versão Estável 2.py` still executes its historical implementation.

Impact: the old GUI can drift if someone changes the historical copy directly.

Invariant until migration: new behavior/bug fixes must originate in `ktools-text`; the legacy copy is frozen as an old compatibility path.

Next: when the traditional Tool surface is migrated to the platform runtime, redirect the GUI/tool path to `ktools-text` and remove or reduce the historical duplicate. Do not block Text Node Pack V1 promotion on a full GUI rewrite.

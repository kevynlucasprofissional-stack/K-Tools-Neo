# Constraints — K-Tools Neo

## Product constraints

- Existing useful utilities must not be removed before an equivalent or superior integrated path is validated.
- The product must remain usable for one-off tasks; workflows are an additional power surface, not a forced complexity tax.
- Real file/media operations may be long-running and must not block the future UI thread.

## Architectural constraints

- The workflow runtime cannot depend on React, React Flow or another editor library.
- Python and Node.js subsystems must be supportable in the same product through explicit adapters/runners.
- Node contracts must be serializable so a visual editor, CLI and future agent can all reason about the same graph.
- Node IDs/types and port names become compatibility-sensitive once published in templates/workflows.
- `Artifact` provenance must be extensible without forcing every node to pass raw filesystem strings only.

## Migration constraints

- `K Tools Neo - Versão Estável 2.py` is legacy/current behavior, not the target architecture.
- Loose root utilities are inventory to classify and migrate incrementally.
- `apps/xcursos-runner` and `apps/yt-dlp-tui` are imported subsystems; avoid duplicating their core logic in K-Tools.

## Delivery constraints

- Feature work occurs on isolated branches/PRs.
- Root-level CI must validate code owned by the monorepo; nested `.github/workflows` inside imported app directories are not sufficient as monorepo CI.

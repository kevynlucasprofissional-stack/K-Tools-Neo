# K-Tools Neo

K-Tools Neo is evolving from a collection of local utilities into a single integrated, local-first automation product.

The target product has two complementary surfaces over the same capabilities:

1. **Tools** — ready-to-use experiences such as convert audio, merge media, create PDFs or download content.
2. **Workflows** — a visual node graph where the same capabilities can be composed into reusable automations.

The architectural rule is simple: **a tool must not own a second implementation of a capability that already exists as a workflow node**. Traditional tools become guided views or templates over the same runtime contracts.

## Repository shape

- `packages/ktools-core/` — typed workflow runtime foundation.
- `apps/xcursos-runner/` — imported XCursos subsystem.
- `apps/yt-dlp-tui/` — imported YouTube subsystem.
- root Python utilities and `K Tools Neo - Versão Estável 2.py` — legacy/current utility inventory to be migrated incrementally, not rewritten wholesale.
- `docs/` — canonical product/engineering context, specs, decisions, testing policy and Engineering Journal.

## Current milestone

The first platform milestone establishes an executable, UI-independent workflow core with typed ports, DAG validation, a node registry, an `Artifact` model, a CLI smoke path and root CI. Real media/file nodes and the visual editor come after this foundation is validated.

See `docs/README.md` for the required read order.

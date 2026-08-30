# Constitution — K-Tools Neo

## Product intent

K-Tools Neo is a single local-first desktop automation platform for files, audio, video, images, PDFs, downloads, text and future AI-assisted operations. It must support both simple ready-made tools and composable visual workflows without duplicating capability implementations.

## Non-negotiable principles

1. **One capability, one owner.** Tool screens and workflows call the same capability/runtime contract.
2. **Runtime before canvas.** The workflow engine must work headlessly and remain independent from any UI framework.
3. **Typed composition.** Nodes expose explicit typed inputs/outputs; invalid connections fail before execution.
4. **Evidence-first evolution.** Specs, tests, CI, native smokes and integration evidence govern claims.
5. **Incremental migration.** Existing utilities remain available until migrated or explicitly superseded.
6. **Local-first by default.** Local files and local execution are primary; network use must be explicit to the capability that needs it.
7. **Observable execution.** Runs must evolve toward reconstructable state, errors, artifacts and provenance.
8. **No silent state loss.** Stateful adapters/runtimes must fail explicitly rather than silently switching to an unrelated fallback.

## Architectural ownership rules

- `ktools-core` owns workflow definitions, graph validation, execution orchestration and core run contracts.
- Node packs own capability definitions and their handlers/adapters.
- Imported applications under `apps/` own their native internals unless a deliberate fork decision supersedes that boundary.
- The future desktop UI owns presentation/editor state, not workflow truth.
- Persistence must have an explicit owner; the UI must not become a second source of truth for run/workflow state.

## Testing / evidence policy

- Core graph rules require unit/contract tests.
- CLI claims require real CLI execution.
- Adapter claims require integration tests and, where relevant, native runtime smokes.
- Visual editor claims require functional UI evidence; screenshots alone do not prove execution.
- Cross-runtime workflow claims require end-to-end evidence across every material boundary.

## Security / privacy

- Never persist tokens, cookies, credentials or secrets in specs, logs, workflows or the Engineering Journal.
- File deletion/mutation nodes must eventually enforce explicit path ownership and safety boundaries.
- Imported applications retain their existing secret-handling rules.

## Compatibility / supported environments

- Windows is the primary desktop target.
- The workflow core should stay cross-platform where doing so does not compromise the Windows product.
- The initial Python core baseline is Python 3.10+.

## Upstream / downstream policy

- Preserve upstream history for imported applications where practical.
- Prefer adapters at the K-Tools boundary over invasive edits to imported subsystems.
- Upstream updates must not silently change K-Tools contracts; adapter tests protect the boundary.

## Scope control

Do not use the platform transition as justification for an unbounded rewrite. Migrate capability by capability behind stable contracts, with tests and rollback paths.

# PLAN / DESIGN: Platform Foundation / Typed Workflow Engine

## 1. Spec of origin

`spec.md`

## 2. Summary of approach

Add a new Python package rather than modifying the legacy GUI. Prove serializable typed graph contracts and headless execution first. Keep real product nodes/adapters as subsequent specs.

## 3. Current state inspected

- baseline ref: `e6fb80f78f4e4e4f943ea6567320161407fe7b5f`;
- legacy GUI: root monolithic Python application;
- imported subsystems: `apps/xcursos-runner`, `apps/yt-dlp-tui`;
- no root CI/canonical platform docs at baseline.

## 4. Architecture

```text
future Desktop UI / CLI / Agent
            |
            v
      WorkflowDefinition
            |
            v
       ktools-core
  +---------+---------+
  | registry/typing   |
  | graph validation  |
  | execution engine  |
  | Artifact contract |
  +---------+---------+
            |
            v
   future Node Packs / Adapters
            |
     +------+------+
     |             |
 Python utils   Node apps
```

## 5. Ownership of state

| State | Owner | Lifetime | Persistence | Recovery |
|---|---|---|---|---|
| workflow definition | caller/schema | workflow | JSON now | reload JSON |
| node definitions | registry/node packs | process | code | re-register |
| node outputs | engine | run | memory only | none in foundation |
| run ID | engine | run | result only | none |
| Artifact identity/provenance | Artifact contract | artifact | serializable | reconstruction from persisted dict later |
| visual canvas state | future UI | view/edit session | TBD | TBD |

## 6. Interfaces / contracts

- `WorkflowDefinition`: nodes + edges.
- `NodeDefinition`: stable type ID + typed input/output ports.
- `NodeHandler(inputs, config, context) -> outputs`.
- `Artifact`: stable ID + data type + URI + provenance/metadata.

## 7. Data flow

Edges resolve source node output ports into target node input ports after validation.

## 8. Control flow

Foundation supports DAG dependency flow only. Branching/conditions/events are deliberately deferred until the base data-flow contract is exercised by real capabilities.

## 9. Lifecycle / idempotence / concurrency

Foundation execution is single-process and sequential in topological order. This intentionally favors deterministic behavior over premature concurrency. Long-running/background execution is a later design.

## 10. Persistence / restart / recovery

Not implemented in this milestone; explicitly recorded as known issue/spec follow-up.

## 11. Security / privacy

Foundation fixtures contain no secrets. Future file and adapter nodes require path/secret boundaries in their own specs.

## 12. Observability

Foundation returns a run ID and per-node outputs. Structured run events/logs are deferred to the persistence/execution-lifecycle spec.

## 13. Compatibility / migration

No existing files are moved or deleted. Legacy and imported apps remain untouched.

## 14. Rollback

Delete the new package/docs/root workflow or revert the feature commit; baseline product behavior is unaffected.

## 15. Validation strategy

- unit/contract tests for graph invariants;
- real CLI smoke;
- root CI across Windows/Ubuntu and Python 3.11/3.13;
- PR diff/integration audit.

## 16. Alternatives considered

1. Continue growing the CustomTkinter monolith.
2. Make the workflow engine TypeScript-first.
3. Fork/extend n8n or Node-RED as the product base.
4. Build Python core + independent future web/desktop editor.

## 17. Alternatives rejected and why

- Monolith growth: conflicts with reuse/composition goal.
- TypeScript-first core: increases friction extracting the majority of current Python utilities before evidence shows the benefit is necessary.
- n8n/Node-RED as base: imports an external product architecture and unnecessary scope; K-Tools needs file/media-local semantics and a smaller ownership surface.

## 18. Risks

See spec risks plus optional-port semantics, schema drift and future async requirements.

## 19. Hypotheses still open

- Exact desktop host and canvas library.
- How much of the legacy GUI can become workflow templates versus dedicated guided views.

# ktools-core

Foundation runtime for K-Tools Neo workflows.

This package is deliberately UI-independent. It defines typed node contracts, workflow graphs, validation, execution and the initial `Artifact` model. The first milestone is intentionally small: prove that the platform can execute a deterministic typed DAG before the visual editor and real media nodes are attached.

## Run locally

```powershell
python -m pip install -e packages/ktools-core
python -m unittest discover -s packages/ktools-core/tests -v
python -m ktools_core packages/ktools-core/examples/hello-workflow.json --json
```

## Current built-in nodes

- `text.literal`
- `text.concat`
- `number.literal`
- `core.identity`

These are validation fixtures, not the final product palette.

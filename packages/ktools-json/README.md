# ktools-json

Official first K-Tools Node Pack: **JSON document split**.

This is the OC-001 proof that a real product capability has exactly one
implementation owner and is callable both directly and as a workflow node.

## Capability

Split a JSON document into parts without breaking its structure:

- finds the main list (the root list, or the largest list reachable through
  object keys);
- `mode="parts"` splits the items into N even parts;
- `mode="size"` splits the items so each chunk stays close to a target size;
- each part is written as a standalone JSON file with the same document
  structure and that list replaced by a subset;
- each written file is re-read and parsed to confirm it is valid JSON;
- results are reported as artifact-shaped records (uri, size, item count).

No external dependencies beyond `ktools-core`. No network, no GUI, no FFmpeg.

## Modules

- `ktools_json.capability` — pure transformation/split-planning owner.
- `ktools_json.writer` — shared file-producing orchestration used by both the
  direct API and the workflow node.
- `ktools_json.api` — public direct API.
- `ktools_json.node` — `json.split` (and `json.literal`) workflow nodes.
- `ktools_json.cli` — headless workflow execution with this node pack.
- `tests/` — capability, API, node, workflow-integration, durable-execution and CLI tests.

## Run

Install `ktools-core` first (this package depends on it):

```powershell
python -m pip install -e packages/ktools-core
python -m pip install -e packages/ktools-json
```

Tests:

```powershell
python -m unittest discover -s packages/ktools-json/tests -v
```

Headless workflow smoke (run from a scratch directory; the example workflow
writes `oc001-split-out/` relative to the current directory):

```powershell
python -m ktools_json packages/ktools-json/examples/split-workflow.json --json
```

To persist the workflow/run/node history and output metadata in SQLite:

```powershell
python -m ktools_json packages/ktools-json/examples/split-workflow.json `
  --json `
  --journal .\ktools-runs.sqlite3
```

The Node Pack does not own durability logic. It uses the optional journal
boundary provided by `ktools-core`, so direct/workflow capability ownership
remains separate from run-history persistence.

## Contract

- Input: a JSON document.
- Config: `mode` (`parts` | `size`, default `parts`); `parts` (positive int,
  default 2); `target_bytes` (positive int, required when `mode="size"`);
  `output_dir` (required); `prefix` (default `json_parte`); `overwrite`
  (default `false`).
- Output: part records `{index, name, uri, sizeBytes, itemCount, kind: "file",
  type: "json"}` plus a `{rootType, listPath, itemCount, partCount,
  outputSizes, estimatedSizes}` summary.
- Failure boundary: typed `JsonSplitError` subclasses (invalid mode/parts/
  target size, no main list, empty root list, source not found, invalid JSON,
  output collision).
- Overwrite: refuses to replace existing part files by default; enable
  `overwrite` explicitly to replace them.
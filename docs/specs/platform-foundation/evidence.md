# Evidence — Platform Foundation

## EV-001 — Local unit/contract suite

Environment: isolated Linux execution sandbox; source imported directly through `PYTHONPATH` because the sandbox blocks package-index network access.

Command:

```text
PYTHONPATH=packages/ktools-core/src python -m unittest discover -s packages/ktools-core/tests -v
```

Observed:

```text
6 tests
OK
```

Claims supported:

- typed DAG happy path;
- incompatible edge rejection;
- cycle rejection;
- missing required input rejection;
- optional unconnected input execution;
- Artifact JSON round-trip.

Claims not supported: editable install, Windows behavior, GitHub CI, real media/adapters.

## EV-002 — Local CLI smoke

Command:

```text
PYTHONPATH=packages/ktools-core/src python -m ktools_core packages/ktools-core/examples/hello-workflow.json --json
```

Observed relevant payload:

```json
{"workflowId":"hello-ktools","nodeOutputs":{"join":{"text":"K-Tools Neo"}}}
```

Exit: 0.

Claim supported: headless CLI reaches the real workflow engine and executes the example DAG.

## EV-003 — Editable-install attempt in sandbox

Classification: HARNESS / ENVIRONMENT, not product failure.

Observed: pip build isolation attempted to reach the package index for setuptools and failed because the sandbox has no network/DNS access.

Follow-up evidence: direct-source tests and CLI smoke passed. Editable installation remains for GitHub CI.

## EV-004 — GitHub Actions

Status: PENDING exact candidate SHA.

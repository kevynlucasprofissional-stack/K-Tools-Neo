# SPEC: Platform Foundation / Typed Workflow Engine

Status: IMPLEMENTING

## 1. Objective

Establish the smallest durable K-Tools Neo platform foundation that can execute a typed workflow independently from the UI and can later host migrated utility capabilities.

## 2. Problem / motivation

K-Tools currently combines a legacy monolithic GUI, loose utilities and mature imported subsystems. Adding more features directly to the monolith would increase duplication and make the planned visual workflow model harder to achieve.

## 3. Current state relevant to this change

At baseline, no shared workflow runtime, node contract, Artifact model, canonical architecture docs or root CI existed.

## 4. Scope

### Included

- serializable workflow/node/edge models;
- typed input/output ports;
- node registry;
- pre-execution graph validation;
- deterministic DAG execution;
- initial Artifact provenance model;
- JSON workflow CLI smoke path;
- root CI for the new core;
- canonical architecture/testing/journal documents.

### Outside this spec

- visual editor;
- media/filesystem/PDF production nodes;
- persistence/restart/cache;
- adapters for imported apps;
- migration of legacy GUI screens;
- AI workflow generation.

## 5. Actors

- K-Tools desktop UI (future client);
- CLI/headless execution;
- node-pack authors;
- future AI/agent workflow composer.

## 6. Scenarios

1. A valid typed DAG is loaded and executes in dependency order.
2. An invalid connection is rejected before handlers run.
3. A cyclic workflow is rejected.
4. A handler failure is surfaced as an execution error bound to a node.
5. A file-like future result can carry stable Artifact identity/provenance.

## 7. Functional requirements

### REQ-001 — Node registry
Priority: MUST

The runtime must register node definitions and handlers by stable type ID.

### REQ-002 — Typed graph validation
Priority: MUST

The runtime must validate node existence, port existence, required connections, duplicate target connections, type compatibility and cycles before execution.

### REQ-003 — Deterministic DAG execution
Priority: MUST

A valid acyclic workflow must execute only after its dependencies and must pass upstream outputs to downstream inputs.

### REQ-004 — Artifact model
Priority: MUST

The core must define an extensible serializable Artifact with identity, type, URI, producer and metadata fields.

### REQ-005 — Headless CLI
Priority: MUST

A JSON workflow must be executable without a desktop UI and return a non-zero code for validation/execution failures.

### REQ-006 — Foundation runtime dependency discipline
Priority: SHOULD

Core graph execution should require no third-party runtime dependency.

### REQ-007 — Root CI
Priority: MUST

The monorepo root must run core installation/tests/CLI smoke on Windows and Ubuntu for supported candidate Python versions.

### REQ-008 — Durable engineering memory
Priority: MUST

Architecture, constraints, current state, decisions, testing policy, known issues, spec/plan/tasks and Engineering Journal must be versioned in the repository.

## 8. Acceptance criteria

### AC-002.1
Given a `number` output connected to a `text` input, when validation runs, then it fails before handler execution with an incompatible-edge error.

### AC-002.2
Given a cyclic graph, when validation runs, then it fails with a cycle error.

### AC-002.3
Given a required input with no edge, validation fails and names the missing node/port.

### AC-003.1
Given two text literal nodes feeding a concat node, execution returns `K-Tools Neo` from the concat node.

### AC-004.1
An Artifact serialized to a dictionary and reconstructed preserves its fields and stable ID.

### AC-005.1
Running the example workflow through `python -m ktools_core ... --json` exits 0 and emits a JSON result containing the workflow ID and node outputs.

### AC-007.1
The exact candidate SHA receives successful root CI jobs on Windows and Ubuntu.

### AC-008.1
A future agent can reconstruct the platform intent, constraints, current state, decisions, evidence policy and known gaps without relying on this chat.

## 9. Non-functional requirements

- deterministic validation/execution order for the same graph;
- clear error categories for validation vs execution;
- Python 3.10+ source compatibility;
- no credentials/secrets in workflow foundation fixtures;
- architecture remains UI-independent.

## 10. Invariants

- Invalid graphs never execute handlers.
- A target input accepts at most one incoming edge in the foundation model.
- The visual editor, when added, cannot become the owner of workflow execution truth.
- Imported app internals are not duplicated into the core.

## 11. Constraints

See `../../CONSTRAINTS.md`.

## 12. Assumptions

- Python remains available in the local K-Tools desktop distribution strategy.
- Multi-runtime adapters can be added without changing the graph semantics.

## 13. Open questions

- Desktop host technology (Tauri/Electron/other).
- React Flow vs alternative canvas after a dedicated UI spike.
- Persistence store and workflow schema versioning strategy.
- Isolation model for third-party/community node packs.

## 14. Risks

- Prematurely freezing node schemas before real media nodes exercise them.
- Treating Artifact as filesystem-only and later blocking remote/virtual artifacts.
- Letting adapter subprocess details leak into generic graph contracts.

## 15. Out-of-scope explicit

No claim is made that the current foundation already integrates legacy utilities or provides a visual n8n-like editor.

## 16. Definition of Done specific

- REQ-001..008 implemented for this milestone;
- local tests and CLI smoke pass;
- exact candidate CI is green;
- PR integration review finds no unclassified material issue;
- canonical docs/journal synchronized.

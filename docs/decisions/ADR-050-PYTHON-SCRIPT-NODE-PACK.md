# ADR 050: Python Script Node Pack (`ktools-script`)

## Date
2026-09-03

## Status
Accepted

## Context
K-Tools Neo provides rich pre-built capabilities for media processing, text, pdf, filesystem, and system execution across 9 official node packs. However, workflows often require custom data shaping, conditional filtering, math formulas, or running specialized existing Python scripts without needing to author and package an entire formal Node Pack.

The project owner requested a dedicated Node Pack called "Script Python" (`script.python_run`) that allows users and agents to embed custom Python logic directly into workflow graphs, accepting upstream port data (`ANY`, `TEXT`, `FILE`, `JSON`) and passing results downstream to other nodes.

## Decision
1. **New Package `packages/ktools-script`**:
   - Implemented `run_python_script` in `ktools_script.runner` providing isolated namespace execution with standard output/error redirection (`io.StringIO`), timing metrics, and structured result extraction.
   - Scripts are provided execution context with `inputs`, `data` (shorthand for `inputs["data"]`), `args`, and mutable `outputs`.
   - Primary `result` is resolved prioritizing `outputs["result"]`, then `namespace["result"]`, falling back to the entire `outputs` dictionary.
   - Registered canonical node `script.python_run` in `ktools_script.node` with `CachePolicy.NEVER`.

2. **Integration into Visual Workflow Studio**:
   - Added `script.python_run` to `catalog.json` with Simple Mode narrative title ("🐍 Script Python") and helpful placeholder code.
   - Created a pre-configured production preset: "🐍 Automação com Script Python (Filtrar e Processar)" connecting `folder.literal` -> `folder.scan_files` -> `script.python_run` -> `system.notify`.

3. **Core Registry & Conformance**:
   - Added `"ktools_script.node"` to `load_all_installed_node_packs` in `ktools_core.registry`.
   - Validated capability presence in `CapabilityManifest`, direct invocation via `CapabilityInvoker`, and multi-step DAG execution in `WorkflowEngine`.

## Consequences
- Workflows gain universal extensibility: any computation or custom Python library can be seamlessly stitched between standard K-Tools nodes.
- Preserves the single-implementation owner invariant: Workflow Studio, Direct API, CLI, and MCP servers all execute through `script.python_run`.
- All output lines (`stdout`, `stderr`, `exit_code`, and `result`) are accessible as distinct typed output ports for downstream branching.

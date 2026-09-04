# Specification: Python Script Node Pack (`ktools-script`)

## Objective
Provide a canonical, secure, and extensible Python Script capability (`script.python_run`) within `packages/ktools-script`, allowing both human users (via Visual Workflow Studio) and AI agents (via Direct API/MCP) to integrate custom Python logic, scripts, and transformations directly into workflow DAGs.

## Architecture & Responsibilities

1. **Package Ownership**:
   - Package: `packages/ktools-script`
   - Node Type ID: `script.python_run`
   - Title: `Executar Script Python` (Narrative: "🐍 Script Python")
   - Category: `Script`
   - Cache Policy: `CachePolicy.NEVER` (scripts may depend on dynamic external state, time, or random functions)

2. **Port Contract**:
   - **Inputs**:
     - `code`: `TEXT` (optional, raw inline Python code)
     - `file_path`: `FILE` (optional, path to an external `.py` file)
     - `data`: `ANY` (optional, primary input data passed from upstream nodes)
     - `args`: `ANY` (optional, additional configuration, dictionary or arguments)
   - **Outputs**:
     - `result`: `ANY` (primary computed result returned by script)
     - `stdout`: `TEXT` (captured standard output text)
     - `stderr`: `TEXT` (captured standard error or exception traceback text)
     - `exit_code`: `NUMBER` (0 for success, 1 on runtime or compilation error)

3. **Execution Semantics**:
   - Either `code` or `file_path` must be provided.
   - Script runs in a controlled dictionary namespace:
     - `inputs`: dict containing all inputs and config values.
     - `data`: shortcut to `inputs.get("data")`.
     - `args`: shortcut to `inputs.get("args")`.
     - `outputs`: dictionary where user scripts can assign arbitrary output variables.
     - `result`: default to `outputs.get("result")`, then `namespace.get("result")`, falling back to `outputs`.
   - Captures `sys.stdout` and `sys.stderr` via `io.StringIO` redirection so `print()` outputs are preserved as node outputs.
   - Measures execution duration in milliseconds.

4. **Integration Surface**:
   - Registered in `ktools_core.registry.load_all_installed_node_packs`.
   - Exposed in `xyflow-editor/src/catalog.json` with Simple Mode narrative fields and syntax-highlighted code editor.
   - Presets: added preset "🐍 Automação com Script Python (Filtrar e Processar)".

## Verification Plan
1. Unit test inline execution with stdout and variable returns.
2. Unit test file execution from external `.py` path.
3. Unit test error capturing (`exit_code=1`, traceback in `stderr`).
4. Conformance verification in `CapabilityManifest` and `CapabilityInvoker`.
5. WorkflowEngine DAG integration test chaining upstream nodes into `script.python_run`.

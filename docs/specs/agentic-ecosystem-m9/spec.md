# Specification: M9 — Agentic Workstation Integration + Capability Ecosystem

## Objective
Deliver:
1. **Hermes Capability Adapter (`ktools_core.adapters.hermes`)**:
   - `HermesCapabilityAdapter`: Translates Hermes action requests into K-Tools capability invocations.
   - Enforces scope constraints and pre-invocation policy handshakes (`PolicyAction.REQUIRE_HUMAN_CONFIRMATION`).
   - Maps `ExecutionReceipt` into Hermes action response structures with artifacts, duration, and receipt token.
2. **Workflow-as-Capability (`ktools_core.adapters.workflow_capability`)**:
   - `register_workflow_as_capability(registry, workflow_def, capability_id, title)`: Wraps a validated `WorkflowDefinition` as an executable node in `NodeRegistry`.
   - Projects input ports from source entry nodes and output ports from terminal nodes.
   - Executes DAG through `WorkflowEngine`, capturing node run logs and publishing final results.
3. **Ecosystem Readiness Inspection (`ktools_core.readiness`)**:
   - `check_readiness(registry)`: Scans registered node packs, host provider capabilities, and external binary dependencies (e.g. ffmpeg, ffprobe, python).
   - Returns typed `ReadinessReport`.
4. **Conformance & Integration Suite**:
   - `test_hermes_workstation_integration.py` proving:
     - Hermes single capability dispatch and receipt translation.
     - Policy handshake halting destructive actions without approval.
     - Execution of a complex multi-node workflow through a single agent action.
     - Readiness inspection.

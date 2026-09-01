from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .cache_identity import (
    ArtifactSnapshotError,
    CacheSignatureUnsupported,
    build_cache_signature,
)
from .cache_store import CacheError, NodeCache, validate_cache_entry
from .diagnostics import DiagnosticKind, DiagnosticSeverity, DiagnosticsSession
from .journal import NullRunJournal, RunEvent, RunEventType, RunJournal
from .models import CachePolicy, NodeDefinition, WorkflowDefinition, is_type_compatible
from .registry import NodeExecutionContext, NodeRegistry


class WorkflowValidationError(ValueError):
    pass


class WorkflowExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    workflow_id: str
    node_outputs: dict[str, dict[str, Any]]


class WorkflowEngine:
    def __init__(
        self,
        registry: NodeRegistry,
        journal: RunJournal | None = None,
        diagnostics: DiagnosticsSession | None = None,
        cache: NodeCache | None = None,
    ) -> None:
        self.registry = registry
        self.journal: RunJournal = journal if journal is not None else NullRunJournal()
        self.diagnostics = diagnostics
        self.cache = cache

    def validate(self, workflow: WorkflowDefinition) -> tuple[str, ...]:
        nodes_by_id = {}
        for node in workflow.nodes:
            if node.id in nodes_by_id:
                raise WorkflowValidationError(f"Duplicate node id: {node.id}")
            nodes_by_id[node.id] = node
            try:
                self.registry.definition(node.type)
            except KeyError as exc:
                raise WorkflowValidationError(str(exc)) from exc

        incoming: dict[tuple[str, str], tuple[str, str]] = {}
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes_by_id}
        indegree: dict[str, int] = {node_id: 0 for node_id in nodes_by_id}

        for edge in workflow.edges:
            if edge.source_node not in nodes_by_id:
                raise WorkflowValidationError(f"Unknown source node: {edge.source_node}")
            if edge.target_node not in nodes_by_id:
                raise WorkflowValidationError(f"Unknown target node: {edge.target_node}")

            source_def = self.registry.definition(nodes_by_id[edge.source_node].type)
            target_def = self.registry.definition(nodes_by_id[edge.target_node].type)

            if edge.source_port not in source_def.outputs:
                raise WorkflowValidationError(
                    f"Unknown output port {edge.source_node}.{edge.source_port}"
                )
            if edge.target_port not in target_def.inputs:
                raise WorkflowValidationError(
                    f"Unknown input port {edge.target_node}.{edge.target_port}"
                )

            source_type = source_def.outputs[edge.source_port].type
            target_type = target_def.inputs[edge.target_port].type
            if not is_type_compatible(source_type, target_type):
                raise WorkflowValidationError(
                    "Incompatible edge "
                    f"{edge.source_node}.{edge.source_port} ({source_type.value}) -> "
                    f"{edge.target_node}.{edge.target_port} ({target_type.value})"
                )

            target_key = (edge.target_node, edge.target_port)
            if target_key in incoming:
                raise WorkflowValidationError(
                    f"Input port already connected: {edge.target_node}.{edge.target_port}"
                )
            incoming[target_key] = (edge.source_node, edge.source_port)

            if edge.target_node not in adjacency[edge.source_node]:
                adjacency[edge.source_node].add(edge.target_node)
                indegree[edge.target_node] += 1

        for node in workflow.nodes:
            definition = self.registry.definition(node.type)
            for port_name, port in definition.inputs.items():
                if port.required and (node.id, port_name) not in incoming:
                    raise WorkflowValidationError(f"Missing required input: {node.id}.{port_name}")

        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while ready:
            node_id = ready.pop(0)
            order.append(node_id)
            for target_id in sorted(adjacency[node_id]):
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    ready.append(target_id)
                    ready.sort()

        if len(order) != len(nodes_by_id):
            raise WorkflowValidationError("Workflow contains a cycle")

        return tuple(order)

    def _record(
        self,
        *,
        run_id: str,
        workflow_id: str,
        event_type: RunEventType,
        node_id: str | None = None,
        node_type: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.journal.record(
            RunEvent.create(
                run_id=run_id,
                workflow_id=workflow_id,
                event_type=event_type,
                node_id=node_id,
                node_type=node_type,
                payload=payload,
            )
        )

    def _diagnose(
        self,
        message: str,
        *,
        run_id: str,
        workflow_id: str,
        node_id: str | None = None,
        severity: DiagnosticSeverity = DiagnosticSeverity.INFO,
        context: dict[str, Any] | None = None,
    ) -> None:
        if self.diagnostics is None:
            return
        self.diagnostics.record(
            message,
            severity=severity,
            kind=DiagnosticKind.LIFECYCLE,
            category="workflow.execution",
            component="ktools-core.engine",
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node_id,
            context=context,
        )

    def _diagnose_cache(
        self,
        message: str,
        *,
        reason: str,
        run_id: str,
        workflow_id: str,
        node_id: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        if self.diagnostics is None:
            return
        self.diagnostics.decision(
            message,
            reason=reason,
            category="workflow.cache",
            component="ktools-core.engine",
            run_id=run_id,
            workflow_id=workflow_id,
            node_id=node_id,
            context=context,
        )

    @staticmethod
    def _validate_node_outputs(
        node_id: str,
        definition: NodeDefinition,
        node_outputs: Any,
    ) -> dict[str, Any]:
        if not isinstance(node_outputs, dict):
            raise WorkflowExecutionError(f"Node {node_id} returned a non-dict output")

        unknown_outputs = set(node_outputs) - set(definition.outputs)
        if unknown_outputs:
            raise WorkflowExecutionError(
                f"Node {node_id} returned unknown outputs: {sorted(unknown_outputs)}"
            )
        missing_outputs = {
            name
            for name, port in definition.outputs.items()
            if port.required and name not in node_outputs
        }
        if missing_outputs:
            raise WorkflowExecutionError(
                f"Node {node_id} omitted required outputs: {sorted(missing_outputs)}"
            )
        return node_outputs

    def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:
        order = self.validate(workflow)
        nodes_by_id = {node.id: node for node in workflow.nodes}
        incoming: dict[tuple[str, str], tuple[str, str]] = {
            (edge.target_node, edge.target_port): (edge.source_node, edge.source_port)
            for edge in workflow.edges
        }
        outputs_by_node: dict[str, dict[str, Any]] = {}
        run_id = f"run_{uuid4().hex}"

        self._record(run_id=run_id, workflow_id=workflow.id, event_type=RunEventType.RUN_STARTED)
        self._diagnose(
            "Workflow run started",
            run_id=run_id,
            workflow_id=workflow.id,
            context={
                "nodeCount": len(workflow.nodes),
                "edgeCount": len(workflow.edges),
                "executionOrder": order,
            },
        )

        for node_id in order:
            node = nodes_by_id[node_id]
            definition = self.registry.definition(node.type)

            try:
                node_inputs: dict[str, Any] = {}
                for port_name in definition.inputs:
                    source = incoming.get((node_id, port_name))
                    if source is None:
                        continue
                    source_node, source_port = source
                    try:
                        node_inputs[port_name] = outputs_by_node[source_node][source_port]
                    except KeyError as exc:
                        raise WorkflowExecutionError(
                            f"Upstream output missing: {source_node}.{source_port}"
                        ) from exc

                cache_signature: str | None = None
                if self.cache is not None:
                    if definition.cache_policy is CachePolicy.NEVER:
                        self._diagnose_cache(
                            "Cache bypassed",
                            reason="node-policy-never",
                            run_id=run_id,
                            workflow_id=workflow.id,
                            node_id=node_id,
                            context={"nodeType": node.type, "nodeVersion": definition.version},
                        )
                    else:
                        try:
                            cache_signature = build_cache_signature(
                                definition,
                                config=dict(node.config),
                                inputs=node_inputs,
                            )
                        except (CacheSignatureUnsupported, ArtifactSnapshotError) as exc:
                            self._diagnose_cache(
                                "Cache bypassed",
                                reason="signature-unsupported",
                                run_id=run_id,
                                workflow_id=workflow.id,
                                node_id=node_id,
                                context={"nodeType": node.type, "detail": str(exc)},
                            )
                        else:
                            try:
                                candidate = self.cache.get(cache_signature)
                            except CacheError as exc:
                                candidate = None
                                self._diagnose_cache(
                                    "Cache lookup failed; executing node",
                                    reason="cache-read-error",
                                    run_id=run_id,
                                    workflow_id=workflow.id,
                                    node_id=node_id,
                                    context={"nodeType": node.type, "detail": str(exc)},
                                )
                            if candidate is None:
                                self._diagnose_cache(
                                    "Cache miss",
                                    reason="signature-not-found",
                                    run_id=run_id,
                                    workflow_id=workflow.id,
                                    node_id=node_id,
                                    context={
                                        "nodeType": node.type,
                                        "nodeVersion": definition.version,
                                        "cacheSignature": cache_signature,
                                    },
                                )
                            else:
                                candidate_usable = True
                                invalid_reason = None
                                invalid_context: dict[str, Any] = {
                                    "cacheSignature": cache_signature,
                                    "originRunId": candidate.origin_run_id,
                                    "originNodeId": candidate.origin_node_id,
                                }
                                if (
                                    candidate.node_type != definition.type_id
                                    or candidate.node_version != definition.version
                                ):
                                    candidate_usable = False
                                    invalid_reason = "metadata-mismatch"
                                else:
                                    validation = validate_cache_entry(candidate)
                                    if not validation.valid:
                                        candidate_usable = False
                                        invalid_reason = validation.artifact_reason or validation.reason
                                        invalid_context["artifactUri"] = validation.artifact_uri

                                if candidate_usable:
                                    try:
                                        cached_outputs = self._validate_node_outputs(
                                            node_id, definition, candidate.outputs
                                        )
                                    except WorkflowExecutionError as exc:
                                        candidate_usable = False
                                        invalid_reason = "cached-output-contract-invalid"
                                        invalid_context["detail"] = str(exc)

                                if candidate_usable:
                                    outputs_by_node[node_id] = cached_outputs
                                    self._record(
                                        run_id=run_id,
                                        workflow_id=workflow.id,
                                        event_type=RunEventType.NODE_CACHED,
                                        node_id=node_id,
                                        node_type=node.type,
                                        payload={
                                            "outputs": cached_outputs,
                                            "cacheSignature": cache_signature,
                                            "originRunId": candidate.origin_run_id,
                                            "originNodeId": candidate.origin_node_id,
                                        },
                                    )
                                    try:
                                        self.cache.mark_used(cache_signature)
                                    except CacheError as exc:
                                        self._diagnose_cache(
                                            "Cache entry reused but usage timestamp update failed",
                                            reason="cache-touch-error",
                                            run_id=run_id,
                                            workflow_id=workflow.id,
                                            node_id=node_id,
                                            context={"detail": str(exc)},
                                        )
                                    self._diagnose_cache(
                                        "Cached node output reused",
                                        reason="validated-cache-hit",
                                        run_id=run_id,
                                        workflow_id=workflow.id,
                                        node_id=node_id,
                                        context={
                                            "nodeType": node.type,
                                            "nodeVersion": definition.version,
                                            "cacheSignature": cache_signature,
                                            "originRunId": candidate.origin_run_id,
                                            "originNodeId": candidate.origin_node_id,
                                        },
                                    )
                                    continue

                                try:
                                    self.cache.invalidate(cache_signature)
                                except CacheError as exc:
                                    invalid_context["invalidationError"] = str(exc)
                                self._diagnose_cache(
                                    "Cache candidate invalid; executing node",
                                    reason=invalid_reason or "candidate-invalid",
                                    run_id=run_id,
                                    workflow_id=workflow.id,
                                    node_id=node_id,
                                    context=invalid_context,
                                )

                self._record(
                    run_id=run_id,
                    workflow_id=workflow.id,
                    event_type=RunEventType.NODE_STARTED,
                    node_id=node_id,
                    node_type=node.type,
                )
                self._diagnose(
                    "Node started",
                    run_id=run_id,
                    workflow_id=workflow.id,
                    node_id=node_id,
                    context={"nodeType": node.type},
                )

                context = NodeExecutionContext(
                    run_id=run_id,
                    workflow_id=workflow.id,
                    node_id=node_id,
                )
                try:
                    raw_outputs = self.registry.execute(
                        node.type,
                        node_inputs,
                        dict(node.config),
                        context,
                    )
                except Exception as exc:
                    raise WorkflowExecutionError(f"Node {node_id} failed: {exc}") from exc

                node_outputs = self._validate_node_outputs(node_id, definition, raw_outputs)
            except Exception as exc:
                self._record(
                    run_id=run_id,
                    workflow_id=workflow.id,
                    event_type=RunEventType.NODE_FAILED,
                    node_id=node_id,
                    node_type=node.type,
                    payload={"errorType": type(exc).__name__, "errorMessage": str(exc)},
                )
                self._record(
                    run_id=run_id,
                    workflow_id=workflow.id,
                    event_type=RunEventType.RUN_FAILED,
                    payload={
                        "errorType": type(exc).__name__,
                        "errorMessage": str(exc),
                        "failedNodeId": node_id,
                        "failedNodeType": node.type,
                    },
                )
                if self.diagnostics is not None:
                    self.diagnostics.capture_exception(
                        exc,
                        "Node execution failed",
                        category="workflow.execution",
                        component="ktools-core.engine",
                        run_id=run_id,
                        workflow_id=workflow.id,
                        node_id=node_id,
                        context={"nodeType": node.type},
                    )
                    self._diagnose(
                        "Workflow run failed",
                        severity=DiagnosticSeverity.ERROR,
                        run_id=run_id,
                        workflow_id=workflow.id,
                        node_id=node_id,
                        context={"failedNodeType": node.type},
                    )
                raise

            outputs_by_node[node_id] = node_outputs
            self._record(
                run_id=run_id,
                workflow_id=workflow.id,
                event_type=RunEventType.NODE_SUCCEEDED,
                node_id=node_id,
                node_type=node.type,
                payload={"outputs": node_outputs},
            )
            self._diagnose(
                "Node succeeded",
                run_id=run_id,
                workflow_id=workflow.id,
                node_id=node_id,
                context={"nodeType": node.type, "outputPorts": sorted(node_outputs)},
            )

            if self.cache is not None and cache_signature is not None:
                try:
                    self.cache.put(
                        signature=cache_signature,
                        node_type=definition.type_id,
                        node_version=definition.version,
                        origin_run_id=run_id,
                        origin_node_id=node_id,
                        outputs=node_outputs,
                    )
                except (CacheError, ArtifactSnapshotError) as exc:
                    self._diagnose_cache(
                        "Node succeeded but cache write was skipped",
                        reason="cache-write-unsupported-or-failed",
                        run_id=run_id,
                        workflow_id=workflow.id,
                        node_id=node_id,
                        context={"nodeType": node.type, "detail": str(exc)},
                    )
                else:
                    self._diagnose_cache(
                        "Node output stored in semantic cache",
                        reason="cache-write-success",
                        run_id=run_id,
                        workflow_id=workflow.id,
                        node_id=node_id,
                        context={
                            "nodeType": node.type,
                            "nodeVersion": definition.version,
                            "cacheSignature": cache_signature,
                        },
                    )

        self._record(run_id=run_id, workflow_id=workflow.id, event_type=RunEventType.RUN_SUCCEEDED)
        self._diagnose("Workflow run succeeded", run_id=run_id, workflow_id=workflow.id)

        return WorkflowResult(
            run_id=run_id,
            workflow_id=workflow.id,
            node_outputs=outputs_by_node,
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .models import WorkflowDefinition, is_type_compatible
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
    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry

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

    def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:
        order = self.validate(workflow)
        nodes_by_id = {node.id: node for node in workflow.nodes}
        incoming: dict[tuple[str, str], tuple[str, str]] = {
            (edge.target_node, edge.target_port): (edge.source_node, edge.source_port)
            for edge in workflow.edges
        }
        outputs_by_node: dict[str, dict[str, Any]] = {}
        run_id = f"run_{uuid4().hex}"

        for node_id in order:
            node = nodes_by_id[node_id]
            definition = self.registry.definition(node.type)
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

            context = NodeExecutionContext(
                run_id=run_id,
                workflow_id=workflow.id,
                node_id=node_id,
            )
            try:
                node_outputs = self.registry.execute(
                    node.type,
                    node_inputs,
                    dict(node.config),
                    context,
                )
            except Exception as exc:
                raise WorkflowExecutionError(f"Node {node_id} failed: {exc}") from exc

            if not isinstance(node_outputs, dict):
                raise WorkflowExecutionError(f"Node {node_id} returned a non-dict output")

            unknown_outputs = set(node_outputs) - set(definition.outputs)
            if unknown_outputs:
                raise WorkflowExecutionError(
                    f"Node {node_id} returned unknown outputs: {sorted(unknown_outputs)}"
                )
            missing_outputs = {
                name for name, port in definition.outputs.items() if port.required and name not in node_outputs
            }
            if missing_outputs:
                raise WorkflowExecutionError(
                    f"Node {node_id} omitted required outputs: {sorted(missing_outputs)}"
                )
            outputs_by_node[node_id] = node_outputs

        return WorkflowResult(
            run_id=run_id,
            workflow_id=workflow.id,
            node_outputs=outputs_by_node,
        )

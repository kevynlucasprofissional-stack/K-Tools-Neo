from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple
from uuid import uuid4

from ..engine import WorkflowEngine
from ..models import (
    CachePolicy,
    DataType,
    NodeDefinition,
    PortDefinition,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)
from ..registry import NodeExecutionContext, NodeRegistry


def register_workflow_as_capability(
    registry: NodeRegistry,
    workflow_def: WorkflowDefinition,
    capability_id: str,
    title: str,
    input_mapping: Dict[str, Tuple[str, str]],
    output_mapping: Dict[str, Tuple[str, str]],
    category: str = "Workflow",
) -> None:
    """Wraps and registers a Workflow DAG definition as a callable Node/Capability."""

    in_ports = {port_name: PortDefinition(DataType.ANY) for port_name in input_mapping}
    out_ports = {port_name: PortDefinition(DataType.ANY) for port_name in output_mapping}

    def _handler(
        inputs: Mapping[str, Any],
        config: Mapping[str, Any],
        context: NodeExecutionContext,
    ) -> Dict[str, Any]:
        merged_inputs = dict(config)
        merged_inputs.update(inputs)

        new_nodes = list(workflow_def.nodes)
        new_edges = list(workflow_def.edges)

        for ext_in, (t_nid, t_port) in input_mapping.items():
            val = merged_inputs.get(ext_in)
            # Check if (t_nid, t_port) already has an incoming edge
            incoming_edge = next(
                (e for e in workflow_def.edges if e.target_node == t_nid and e.target_port == t_port),
                None,
            )
            if incoming_edge:
                for i, n in enumerate(new_nodes):
                    if n.id == incoming_edge.source_node:
                        cfg = dict(n.config)
                        cfg[incoming_edge.source_port] = val
                        cfg["value"] = val
                        new_nodes[i] = WorkflowNode(id=n.id, type=n.type, config=cfg)
            else:
                feeder_id = f"_feeder_{ext_in}_{uuid4().hex[:6]}"
                new_nodes.append(WorkflowNode(id=feeder_id, type="core.literal", config={"value": val}))
                new_edges.append(
                    WorkflowEdge(
                        source_node=feeder_id,
                        source_port="value",
                        target_node=t_nid,
                        target_port=t_port,
                    )
                )

        instance_wf = WorkflowDefinition(
            id=f"{workflow_def.id}_{uuid4().hex[:8]}",
            nodes=tuple(new_nodes),
            edges=tuple(new_edges),
        )

        engine = WorkflowEngine(registry)
        run_res = engine.execute(instance_wf)

        res_outputs: Dict[str, Any] = {}
        for ext_out, (s_nid, s_port) in output_mapping.items():
            if s_nid in run_res.node_outputs and s_port in run_res.node_outputs[s_nid]:
                res_outputs[ext_out] = run_res.node_outputs[s_nid][s_port]

        return res_outputs

    node_def = NodeDefinition(
        type_id=capability_id,
        title=title,
        category=category,
        inputs=in_ports,
        outputs=out_ports,
        version="1",
        cache_policy=CachePolicy.NEVER,
    )

    registry.register(node_def, _handler)

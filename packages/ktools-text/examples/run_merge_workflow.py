from __future__ import annotations

import json
import sys
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_text.node import NODE_TYPE_ID, register_nodes


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_merge_workflow.py OUTPUT.md")
    here = Path(__file__).resolve().parent
    output = Path(argv[1]).expanduser().resolve()

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="text-merge-smoke",
        nodes=(
            WorkflowNode(
                id="source",
                type="files.literal",
                config={"paths": [str(here / "source-a.md"), str(here / "source-b.txt")]},
            ),
            WorkflowNode(
                id="merge",
                type=NODE_TYPE_ID,
                config={"output_path": str(output), "separator_mode": "nenhum"},
            ),
        ),
        edges=(
            WorkflowEdge(
                source_node="source",
                source_port="files",
                target_node="merge",
                target_port="files",
            ),
        ),
    )
    result = WorkflowEngine(registry).execute(workflow)
    artifact = result.node_outputs["merge"]["file"]
    print(json.dumps(artifact.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

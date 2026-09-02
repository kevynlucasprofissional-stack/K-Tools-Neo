from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfWriter

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_pdf.node import NODE_TYPE_ID, register_nodes


def _fixture(path: Path, width: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=width, height=300)
    with path.open("wb") as handle:
        writer.write(handle)
    writer.close()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_merge_workflow.py OUTPUT.pdf")
    output = Path(sys.argv[1]).resolve()
    first = output.parent / "source-a.pdf"
    second = output.parent / "source-b.pdf"
    _fixture(first, 101)
    _fixture(second, 201)

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="pdf-smoke",
        nodes=(
            WorkflowNode(id="source", type="files.literal", config={"paths": [str(first), str(second)]}),
            WorkflowNode(id="merge", type=NODE_TYPE_ID, config={"output_path": str(output)}),
        ),
        edges=(WorkflowEdge(source_node="source", source_port="files", target_node="merge", target_port="files"),),
    )
    result = WorkflowEngine(registry).execute(workflow)
    print(result.node_outputs["merge"]["pdf"].uri)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

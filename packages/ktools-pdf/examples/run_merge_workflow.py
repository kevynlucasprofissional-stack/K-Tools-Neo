from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfWriter

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_pdf.node import NODE_TYPE_ID, register_nodes


def _make_pdf(path: Path, sizes: list[tuple[float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    try:
        for width, height in sizes:
            writer.add_blank_page(width=width, height=height)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_merge_workflow.py OUTPUT.pdf")

    output = Path(argv[1]).expanduser().resolve()
    source_dir = output.parent / "pdf-smoke-inputs"
    first = source_dir / "source-a.pdf"
    second = source_dir / "source-b.pdf"
    _make_pdf(first, [(101, 201), (102, 202)])
    _make_pdf(second, [(301, 401)])

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="pdf-merge-smoke",
        nodes=(
            WorkflowNode(
                id="source",
                type="files.literal",
                config={"paths": [str(first), str(second)]},
            ),
            WorkflowNode(
                id="merge",
                type=NODE_TYPE_ID,
                config={"output_path": str(output)},
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
    artifact = result.node_outputs["merge"]["pdf"]
    print(json.dumps(artifact.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

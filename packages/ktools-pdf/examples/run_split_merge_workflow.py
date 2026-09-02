from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_pdf.node import register_nodes


def make_pdf(path: Path) -> list[tuple[float, float]]:
    expected = [(101.0, 201.0), (102.0, 202.0), (103.0, 203.0), (104.0, 204.0), (105.0, 205.0)]
    writer = PdfWriter()
    try:
        for width, height in expected:
            writer.add_blank_page(width=width, height=height)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()
    return expected


def dimensions(path: Path) -> list[tuple[float, float]]:
    reader = PdfReader(str(path), strict=False)
    try:
        return [(float(page.mediabox.width), float(page.mediabox.height)) for page in reader.pages]
    finally:
        stream = getattr(reader, "stream", None)
        close = getattr(stream, "close", None)
        if callable(close):
            close()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_split_merge_workflow.py OUTPUT_DIR")

    root = Path(argv[1]).expanduser().resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    source = root / "source.pdf"
    parts_dir = root / "parts"
    recomposed = root / "recomposed.pdf"
    expected = make_pdf(source)

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="pdf-split-merge-smoke",
        nodes=(
            WorkflowNode(id="source", type="file.literal", config={"path": str(source)}),
            WorkflowNode(id="split", type="pdf.split.parts", config={"output_dir": str(parts_dir), "parts": 3}),
            WorkflowNode(id="merge", type="pdf.merge.files", config={"output_path": str(recomposed)}),
        ),
        edges=(
            WorkflowEdge(source_node="source", source_port="file", target_node="split", target_port="file"),
            WorkflowEdge(source_node="split", source_port="files", target_node="merge", target_port="files"),
        ),
    )
    result = WorkflowEngine(registry).execute(workflow)

    part_artifacts = result.node_outputs["split"]["files"]
    part_paths = [path_from_file_uri(artifact.uri) for artifact in part_artifacts]
    part_dimensions = [dimensions(path) for path in part_paths]
    expected_parts = [expected[:2], expected[2:4], expected[4:]]
    if part_dimensions != expected_parts:
        raise AssertionError(f"unexpected split page ranges: {part_dimensions!r}")
    if dimensions(recomposed) != expected:
        raise AssertionError(f"recomposed PDF does not preserve source order: {dimensions(recomposed)!r}")

    print(
        json.dumps(
            {
                "workflowId": result.workflow_id,
                "runId": result.run_id,
                "parts": [artifact.to_dict() for artifact in part_artifacts],
                "recomposed": result.node_outputs["merge"]["pdf"].to_dict(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

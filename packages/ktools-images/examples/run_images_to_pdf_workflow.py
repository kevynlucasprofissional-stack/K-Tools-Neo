from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_images.node import IMAGES_TO_PDF_NODE_TYPE_ID, register_nodes


def _make_sources(root: Path) -> tuple[Path, Path]:
    rgb = root / "portrait.png"
    alpha = root / "landscape.png"
    first = Image.new("RGB", (10, 20), (11, 22, 33))
    second = Image.new("RGBA", (30, 10), (101, 121, 141, 77))
    try:
        first.save(rgb, "PNG")
        second.save(alpha, "PNG")
    finally:
        first.close()
        second.close()
    return rgb, alpha


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_images_to_pdf_workflow.py OUTPUT_DIR")

    root = Path(argv[1]).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    rgb, alpha = _make_sources(root)
    output = root / "images.pdf"

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="images-to-pdf-smoke",
        nodes=(
            WorkflowNode(id="source", type="files.literal", config={"paths": [str(rgb), str(alpha)]}),
            WorkflowNode(id="pdf", type=IMAGES_TO_PDF_NODE_TYPE_ID, config={"output_file": str(output)}),
        ),
        edges=(
            WorkflowEdge(source_node="source", source_port="files", target_node="pdf", target_port="files"),
        ),
    )

    result = WorkflowEngine(registry).execute(workflow)
    artifact = result.node_outputs["pdf"]["pdf"]
    if artifact.type is not DataType.PDF or artifact.mime_type != "application/pdf":
        raise AssertionError(artifact.to_dict())

    path = path_from_file_uri(artifact.uri)
    pdf = PdfReader(str(path), strict=False)
    ratios = [float(page.mediabox.width) / float(page.mediabox.height) for page in pdf.pages]
    if len(ratios) != 2:
        raise AssertionError(ratios)
    if not math.isclose(ratios[0], 0.5, rel_tol=0.03, abs_tol=0.03):
        raise AssertionError(ratios)
    if not math.isclose(ratios[1], 3.0, rel_tol=0.03, abs_tol=0.03):
        raise AssertionError(ratios)

    metadata = dict(artifact.metadata)
    if metadata.get("sourceNames") != [rgb.name, alpha.name]:
        raise AssertionError(metadata)
    if metadata.get("pageCount") != 2 or metadata.get("sourceCount") != 2:
        raise AssertionError(metadata)
    if metadata.get("alphaBackground") != "white" or metadata.get("outputMode") != "RGB":
        raise AssertionError(metadata)
    if metadata.get("pageSizes") != [[10, 20], [30, 10]]:
        raise AssertionError(metadata)

    print(
        json.dumps(
            {
                "runId": result.run_id,
                "pdf": artifact.to_dict(),
                "pageRatios": ratios,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

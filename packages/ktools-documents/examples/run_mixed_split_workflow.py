from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_documents.node import DOCUMENT_SPLIT_NODE_TYPE_ID, register_nodes


def _make_pdf(path: Path) -> None:
    writer = PdfWriter()
    try:
        writer.add_blank_page(width=101, height=201)
        writer.add_blank_page(width=102, height=202)
        writer.add_blank_page(width=103, height=203)
        writer.add_blank_page(width=104, height=204)
        with path.open("wb") as handle:
            writer.write(handle)
    finally:
        close = getattr(writer, "close", None)
        if callable(close):
            close()


def _pdf_dims(path: Path) -> list[tuple[float, float]]:
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
        raise SystemExit("usage: run_mixed_split_workflow.py OUTPUT_DIR")
    root = Path(argv[1]).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    text = root / "notes.md"
    text.write_text("alpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
    pdf = root / "pages.pdf"
    _make_pdf(pdf)
    ignored = root / "ignore.bin"
    ignored.write_bytes(b"ignored")
    output_dir = root / "parts"

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="documents-mixed-split-smoke",
        nodes=(
            WorkflowNode(id="source", type="files.literal", config={"paths": [str(text), str(ignored), str(pdf)]}),
            WorkflowNode(id="split", type=DOCUMENT_SPLIT_NODE_TYPE_ID, config={"output_dir": str(output_dir), "parts": 2}),
        ),
        edges=(WorkflowEdge(source_node="source", source_port="files", target_node="split", target_port="files"),),
    )
    result = WorkflowEngine(registry).execute(workflow)
    files = result.node_outputs["split"]["files"]
    report = result.node_outputs["split"]["report"]

    if (report["inputCount"], report["outputCount"], report["errorCount"]) != (2, 4, 0):
        raise AssertionError(report)
    if [item.type for item in files] != [DataType.FILE, DataType.FILE, DataType.PDF, DataType.PDF]:
        raise AssertionError([item.type for item in files])

    text_parts = [path_from_file_uri(item.uri) for item in files[:2]]
    pdf_parts = [path_from_file_uri(item.uri) for item in files[2:]]
    if "".join(path.read_text(encoding="utf-8") for path in text_parts) != text.read_text(encoding="utf-8"):
        raise AssertionError("text parts did not reconstruct source")
    dims = [_pdf_dims(path) for path in pdf_parts]
    if dims != [[(101.0, 201.0), (102.0, 202.0)], [(103.0, 203.0), (104.0, 204.0)]]:
        raise AssertionError(dims)

    print(json.dumps({"runId": result.run_id, "report": report, "files": [item.to_dict() for item in files]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

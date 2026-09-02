from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import DataType, WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_images.node import WEBP_TO_PNG_NODE_TYPE_ID, register_nodes


def _make_sources(root: Path) -> tuple[Path, Path]:
    rgb = root / "rgb.webp"
    alpha = root / "alpha.webp"
    first = Image.new("RGB", (3, 2), (11, 22, 33))
    second = Image.new("RGBA", (2, 3), (101, 121, 141, 77))
    try:
        first.save(rgb, "WEBP", lossless=True)
        second.save(alpha, "WEBP", lossless=True)
    finally:
        first.close()
        second.close()
    return rgb, alpha


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_webp_to_png_workflow.py OUTPUT_DIR")

    root = Path(argv[1]).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    rgb, alpha = _make_sources(root)
    output_dir = root / "png"

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="webp-to-png-smoke",
        nodes=(
            WorkflowNode(id="source", type="files.literal", config={"paths": [str(rgb), str(alpha)]}),
            WorkflowNode(id="convert", type=WEBP_TO_PNG_NODE_TYPE_ID, config={"output_dir": str(output_dir)}),
        ),
        edges=(
            WorkflowEdge(source_node="source", source_port="files", target_node="convert", target_port="files"),
        ),
    )

    result = WorkflowEngine(registry).execute(workflow)
    outputs = result.node_outputs["convert"]["files"]
    if [item.type for item in outputs] != [DataType.IMAGE, DataType.IMAGE]:
        raise AssertionError([item.type for item in outputs])

    snapshots = []
    for artifact in outputs:
        path = path_from_file_uri(artifact.uri)
        with Image.open(path) as image:
            image.load()
            snapshots.append((image.mode, image.size, list(image.getdata())))

    if snapshots[0] != ("RGB", (3, 2), [(11, 22, 33)] * 6):
        raise AssertionError(snapshots[0])
    if snapshots[1] != ("RGBA", (2, 3), [(101, 121, 141, 77)] * 6):
        raise AssertionError(snapshots[1])

    print(
        json.dumps(
            {
                "runId": result.run_id,
                "files": [item.to_dict() for item in outputs],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

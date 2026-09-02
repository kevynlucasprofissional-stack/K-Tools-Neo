from __future__ import annotations

import json
import sys
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine
from ktools_core.local_files import path_from_file_uri
from ktools_core.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from ktools_core.registry import NodeRegistry
from ktools_text.node import SPLIT_NODE_TYPE_ID, register_nodes


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: run_split_merge_workflow.py OUTPUT_DIR")

    root = Path(argv[1]).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    source = root / "source.md"
    parts_dir = root / "parts"
    merged = root / "merged.md"
    source_text = "alpha\nbbbb\ncc\nddddd\nomega\n"
    source.write_text(source_text, encoding="utf-8", newline="")

    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    workflow = WorkflowDefinition(
        id="text-split-merge-smoke",
        nodes=(
            WorkflowNode(id="source", type="file.literal", config={"path": str(source)}),
            WorkflowNode(
                id="split",
                type=SPLIT_NODE_TYPE_ID,
                config={"output_dir": str(parts_dir), "parts": 3},
            ),
            WorkflowNode(
                id="merge",
                type="text.merge.files",
                config={"output_path": str(merged), "separator_mode": "nenhum"},
            ),
        ),
        edges=(
            WorkflowEdge(source_node="source", source_port="file", target_node="split", target_port="file"),
            WorkflowEdge(source_node="split", source_port="files", target_node="merge", target_port="files"),
        ),
    )

    result = WorkflowEngine(registry).execute(workflow)
    artifacts = result.node_outputs["split"]["files"]
    part_paths = [path_from_file_uri(artifact.uri) for artifact in artifacts]
    part_texts = [path.read_text(encoding="utf-8") for path in part_paths]

    if len(part_paths) != 3:
        raise AssertionError(f"expected 3 parts, got {len(part_paths)}")
    if "".join(part_texts) != source_text:
        raise AssertionError("ordered split parts do not reconstruct the decoded source")

    expected_merged = "".join(part + "\n\n" for part in part_texts)
    actual_merged = merged.read_text(encoding="utf-8")
    if actual_merged != expected_merged:
        raise AssertionError(
            f"downstream merge mismatch: expected={expected_merged!r} actual={actual_merged!r}"
        )

    print(
        json.dumps(
            {
                "runId": result.run_id,
                "parts": [artifact.to_dict() for artifact in artifacts],
                "merged": result.node_outputs["merge"]["file"].to_dict(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

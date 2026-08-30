from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .builtin import register_builtin_nodes
from .engine import WorkflowEngine, WorkflowExecutionError, WorkflowValidationError
from .models import Artifact, WorkflowDefinition
from .registry import NodeRegistry


def _jsonable(value: Any) -> Any:
    if isinstance(value, Artifact):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def build_engine() -> WorkflowEngine:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    return WorkflowEngine(registry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute a K-Tools Neo workflow JSON file")
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    raw = json.loads(args.workflow.read_text(encoding="utf-8"))
    workflow = WorkflowDefinition.from_dict(raw)

    try:
        result = build_engine().execute(workflow)
    except WorkflowValidationError as exc:
        print(f"VALIDATION_ERROR: {exc}")
        return 2
    except WorkflowExecutionError as exc:
        print(f"EXECUTION_ERROR: {exc}")
        return 3

    payload = {
        "runId": result.run_id,
        "workflowId": result.workflow_id,
        "nodeOutputs": _jsonable(result.node_outputs),
    }
    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Workflow {result.workflow_id} completed: {result.run_id}")
    return 0

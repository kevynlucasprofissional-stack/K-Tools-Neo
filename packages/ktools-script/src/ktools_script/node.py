from __future__ import annotations

from typing import Any, Mapping

from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .runner import run_python_script


def register_nodes(registry: NodeRegistry) -> None:
    node_def = NodeDefinition(
        type_id="script.python_run",
        title="Executar Script Python",
        category="Script",
        inputs={
            "code": PortDefinition(DataType.TEXT, required=False),
            "file_path": PortDefinition(DataType.FILE, required=False),
            "data": PortDefinition(DataType.ANY, required=False),
            "args": PortDefinition(DataType.ANY, required=False),
        },
        outputs={
            "result": PortDefinition(DataType.ANY),
            "stdout": PortDefinition(DataType.TEXT),
            "stderr": PortDefinition(DataType.TEXT),
            "exit_code": PortDefinition(DataType.NUMBER),
        },
        version="1",
        cache_policy=CachePolicy.NEVER,
    )

    registry.register(node_def, _python_script_handler)


def _python_script_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    code = inputs.get("code") or config.get("code")
    file_path = inputs.get("file_path") or config.get("file_path")

    merged_inputs = dict(config)
    merged_inputs.update(inputs)

    res = run_python_script(
        code=code,
        file_path=file_path,
        inputs=merged_inputs,
    )

    return {
        "result": res.result,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "exit_code": res.exit_code,
    }

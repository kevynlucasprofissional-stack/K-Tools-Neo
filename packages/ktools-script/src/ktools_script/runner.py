from __future__ import annotations

import io
import os
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class ScriptExecutionResult:
    exit_code: int
    result: Any = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    outputs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "result": self.result,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "outputs": self.outputs,
        }


def run_python_script(
    code: Optional[str] = None,
    file_path: Optional[Union[str, Path]] = None,
    inputs: Optional[Dict[str, Any]] = None,
    timeout_seconds: float = 30.0,
) -> ScriptExecutionResult:
    """Executes inline Python code or an external .py file within a controlled scope.

    The script receives:
      - `inputs`: dictionary of all input ports and configs.
      - `data`: shortcut to inputs.get("data").
      - `args`: shortcut to inputs.get("args").
      - `outputs`: dictionary to write named output ports into (e.g. outputs["result"] = ...).
    """
    script_source = code
    if file_path:
        p = Path(file_path).resolve()
        if not p.is_file():
            return ScriptExecutionResult(
                exit_code=1,
                stderr=f"Arquivo de script Python não encontrado: {file_path}",
            )
        script_source = p.read_text(encoding="utf-8")

    if not script_source:
        return ScriptExecutionResult(
            exit_code=1,
            stderr="Nenhum código ou arquivo Python foi fornecido para execução.",
        )

    start_time = time.perf_counter()
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    user_inputs = inputs or {}
    user_outputs: Dict[str, Any] = {}

    namespace: Dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(file_path) if file_path else "<inline-script>",
        "inputs": user_inputs,
        "data": user_inputs.get("data"),
        "args": user_inputs.get("args"),
        "outputs": user_outputs,
        "result": None,
    }

    exit_code = 0
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            compiled = compile(script_source, namespace["__file__"], "exec")
            exec(compiled, namespace)
    except Exception as exc:
        exit_code = 1
        traceback.print_exc(file=stderr_buf)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Determine primary result
    primary_result = user_outputs.get("result")
    if primary_result is None:
        primary_result = namespace.get("result")
    if primary_result is None:
        primary_result = user_outputs

    return ScriptExecutionResult(
        exit_code=exit_code,
        result=primary_result,
        stdout=stdout_buf.getvalue(),
        stderr=stderr_buf.getvalue(),
        duration_ms=duration_ms,
        outputs=user_outputs,
    )

from __future__ import annotations

from typing import Any, Mapping

from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .clipboard import get_clipboard, set_clipboard
from .events import get_system_event_stream
from .health import get_host_health
from .process import launch_process


def register_nodes(registry: NodeRegistry) -> None:
    # 1. Process Launch
    registry.register(
        NodeDefinition(
            type_id="system.process_launch",
            title="Executar Processo do Sistema",
            category="System",
            inputs={
                "command": PortDefinition(DataType.ANY, required=True),
                "cwd": PortDefinition(DataType.FOLDER, required=False),
                "timeout_seconds": PortDefinition(DataType.NUMBER, required=False),
            },
            outputs={
                "exit_code": PortDefinition(DataType.NUMBER),
                "stdout": PortDefinition(DataType.TEXT),
                "stderr": PortDefinition(DataType.TEXT),
                "timed_out": PortDefinition(DataType.BOOLEAN),
                "duration_ms": PortDefinition(DataType.NUMBER),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _process_launch_handler,
    )

    # 2. Clipboard Read
    registry.register(
        NodeDefinition(
            type_id="system.clipboard_read",
            title="Ler Área de Transferência",
            category="System",
            inputs={},
            outputs={
                "text": PortDefinition(DataType.TEXT),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _clipboard_read_handler,
    )

    # 3. Clipboard Write
    registry.register(
        NodeDefinition(
            type_id="system.clipboard_write",
            title="Gravar na Área de Transferência",
            category="System",
            inputs={
                "text": PortDefinition(DataType.TEXT, required=True),
            },
            outputs={
                "success": PortDefinition(DataType.BOOLEAN),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _clipboard_write_handler,
    )

    # 4. Host Health
    registry.register(
        NodeDefinition(
            type_id="system.host_health",
            title="Diagnóstico de Saúde do Host",
            category="System",
            inputs={
                "path": PortDefinition(DataType.TEXT, required=False),
            },
            outputs={
                "platform": PortDefinition(DataType.TEXT),
                "python_version": PortDefinition(DataType.TEXT),
                "cpu_count": PortDefinition(DataType.NUMBER),
                "disk_usage": PortDefinition(DataType.JSON),
                "health": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _host_health_handler,
    )

    # 5. System Notify
    registry.register(
        NodeDefinition(
            type_id="system.notify",
            title="Notificação do Sistema",
            category="System",
            inputs={
                "title": PortDefinition(DataType.TEXT, required=True),
                "message": PortDefinition(DataType.TEXT, required=True),
                "level": PortDefinition(DataType.TEXT, required=False),
            },
            outputs={
                "delivered": PortDefinition(DataType.BOOLEAN),
                "event_id": PortDefinition(DataType.TEXT),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _notify_handler,
    )


def _process_launch_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    cmd = inputs.get("command") or config.get("command")
    cwd = inputs.get("cwd") or config.get("cwd")
    timeout = inputs.get("timeout_seconds") or config.get("timeout_seconds") or 30.0

    res = launch_process(command=cmd, cwd=cwd, timeout_seconds=float(timeout))

    # Emit system event for process termination/failure
    evt_type = "process.success" if res["exit_code"] == 0 else "process.error"
    get_system_event_stream().emit(
        event_type=evt_type,
        message=f"Process exited with code {res['exit_code']}",
        payload={"exit_code": res["exit_code"], "duration_ms": res["duration_ms"], "timed_out": res["timed_out"]},
    )

    return {
        "exit_code": res["exit_code"],
        "stdout": res["stdout"],
        "stderr": res["stderr"],
        "timed_out": res["timed_out"],
        "duration_ms": res["duration_ms"],
    }


def _clipboard_read_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    return {"text": get_clipboard()}


def _clipboard_write_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    text = inputs.get("text", "")
    set_clipboard(str(text))
    return {"success": True}


def _host_health_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    path = inputs.get("path") or config.get("path")
    h = get_host_health(path)
    return {
        "platform": h["platform"],
        "python_version": h["python_version"],
        "cpu_count": h["cpu_count"],
        "disk_usage": h["disk"],
        "health": h,
    }


def _notify_handler(
    inputs: Mapping[str, Any],
    config: Mapping[str, Any],
    context: NodeExecutionContext,
) -> dict[str, Any]:
    title = inputs.get("title") or config.get("title") or "K-Tools Notification"
    message = inputs.get("message") or config.get("message") or ""
    level = inputs.get("level") or config.get("level") or "info"

    evt = get_system_event_stream().emit(
        event_type=f"notification.{level}",
        message=f"{title}: {message}",
        payload={"title": title, "message": message, "level": level},
    )

    return {
        "delivered": True,
        "event_id": evt.event_id,
    }

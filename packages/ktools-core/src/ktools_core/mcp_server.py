from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ktools_core.invoker import CapabilityInvoker
from ktools_core.manifest import generate_capability_manifest
from ktools_core.registry import NodeRegistry


def _to_mcp_tool_name(capability_id: str) -> str:
    return capability_id.replace(".", "_")


def _from_mcp_tool_name(tool_name: str, registry: NodeRegistry) -> str:
    # Direct match if type_id is already in registry
    if tool_name in registry.definitions:
        return tool_name
    # Search definitions for matching sanitized name
    for type_id in registry.definitions:
        if _to_mcp_tool_name(type_id) == tool_name:
            return type_id
    return tool_name.replace("_", ".")


def _datatype_to_json_schema(data_type: str) -> Dict[str, Any]:
    dt = data_type.lower()
    if dt in ("string", "text", "file", "url", "audio", "video", "image", "pdf", "folder"):
        return {"type": "string"}
    if dt == "number":
        return {"type": "number"}
    if dt == "boolean":
        return {"type": "boolean"}
    if dt in ("file_set", "files"):
        return {"type": "array", "items": {"type": "string"}}
    if dt in ("json", "dict", "object"):
        return {"type": "object"}
    return {}


class KToolsMCPServer:
    def __init__(self, registry: NodeRegistry, invoker: Optional[CapabilityInvoker] = None) -> None:
        self.registry = registry
        self.invoker = invoker or CapabilityInvoker(registry)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        if method == "tools/list":
            return self._handle_tools_list(req_id)
        elif method == "tools/call":
            return self._handle_tools_call(req_id, params)
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }

    def _handle_tools_list(self, req_id: Any) -> Dict[str, Any]:
        manifest = generate_capability_manifest(self.registry)
        tools = []

        for cap_id, cap in manifest.capabilities.items():
            properties = {}
            required = []
            for p_name, port in cap.inputs.items():
                schema = _datatype_to_json_schema(port.data_type)
                if port.description:
                    schema["description"] = port.description
                properties[p_name] = schema
                if port.required:
                    required.append(p_name)

            tool_obj = {
                "name": _to_mcp_tool_name(cap_id),
                "description": cap.description or f"{cap.title} ({cap.category})",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
            tools.append(tool_obj)

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": sorted(tools, key=lambda t: t["name"]),
            },
        }

    def _handle_tools_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}

        capability_id = _from_mcp_tool_name(tool_name, self.registry)
        receipt = self.invoker.invoke(capability_id, inputs=arguments)

        is_error = receipt.status.value == "FAILED"
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": receipt.to_json(),
                    }
                ],
                "isError": is_error,
            },
        }

from __future__ import annotations

from typing import Any, Dict, Optional

from ..invoker import CapabilityInvoker
from ..manifest import generate_capability_manifest
from ..registry import NodeRegistry


class HermesCapabilityAdapter:
    """Translates external Hermes Workstation action requests into canonical K-Tools capability invocations."""

    def __init__(self, registry: NodeRegistry, invoker: CapabilityInvoker) -> None:
        self.registry = registry
        self.invoker = invoker

    def dispatch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        action = request.get("action")
        if not action:
            return {"status": "ERROR", "error": "Action identifier required"}

        parameters = request.get("parameters", {})
        caller_scope = request.get("caller_scope", {})
        human_confirmed = request.get("human_confirmed", False)

        # 1. CapabilityScope validation
        if caller_scope.get("allow_subprocess") is False and action == "system.process_launch":
            return {
                "status": "DENIED",
                "error": "Operation denied by CapabilityScope: allow_subprocess=False",
            }

        # 2. Policy action evaluation / confirmation handshake
        side_effect_class = request.get("side_effect_class")
        if not side_effect_class:
            manifest = generate_capability_manifest(self.registry)
            cap_def = manifest.capabilities.get(action)
            if cap_def:
                side_effect_class = cap_def.side_effect_class.value

        sec = (side_effect_class or "").lower()
        if sec == "destructive_mutation" and not human_confirmed:
            if not caller_scope.get("allow_destructive", False):
                return {
                    "status": "REQUIRES_CONFIRMATION",
                    "policy_action": "require_human_confirmation",
                    "action": action,
                    "parameters": parameters,
                    "message": "Action requires explicit human confirmation before execution",
                }

        # 3. Canonical Capability Invocation
        receipt = self.invoker.invoke(action, inputs=parameters)
        duration_ms = round(receipt.duration_seconds * 1000, 2)

        if receipt.status.value == "SUCCESS":
            return {
                "status": "SUCCESS",
                "receipt_id": receipt.receipt_id,
                "action": receipt.capability_id,
                "outputs": receipt.outputs,
                "artifacts": [a.to_dict() for a in receipt.artifacts],
                "duration_ms": duration_ms,
                "timestamp": receipt.started_at,
            }
        else:
            err_msg = receipt.error.get("message") if receipt.error else "Capability execution failed"
            return {
                "status": receipt.status.value,
                "receipt_id": receipt.receipt_id,
                "action": receipt.capability_id,
                "error": err_msg,
                "duration_ms": duration_ms,
            }

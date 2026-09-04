from __future__ import annotations

import sys
import shutil
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from .registry import NodeRegistry
from .host import get_active_host_provider


@dataclass
class ReadinessReport:
    status: str
    node_pack_count: int
    capability_count: int
    dependencies: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "node_pack_count": self.node_pack_count,
            "capability_count": self.capability_count,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp,
        }


def check_readiness(registry: NodeRegistry) -> ReadinessReport:
    """Evaluates readiness of K-Tools Neo capabilities, node packs, and system dependencies."""
    type_ids = registry.type_ids()
    capability_count = len(type_ids)

    # Count distinct capability prefixes/families
    prefixes = set()
    for tid in type_ids:
        prefix = tid.split(".")[0]
        prefixes.add(prefix)
    node_pack_count = len(prefixes)

    # Inspect dependencies
    provider = get_active_host_provider()
    deps: Dict[str, Dict[str, Any]] = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "ready": True,
        },
        "host_provider": {
            "name": provider.name,
            "platform": provider.platform.value,
            "capabilities": [c.value for c in provider.supported_capabilities()],
            "ready": True,
        },
        "ffmpeg": {
            "available": shutil.which("ffmpeg") is not None,
            "path": shutil.which("ffmpeg") or "",
        },
        "ffprobe": {
            "available": shutil.which("ffprobe") is not None,
            "path": shutil.which("ffprobe") or "",
        },
    }

    # If base core capabilities are available, runtime is READY
    is_ready = capability_count >= 30
    status = "READY" if is_ready else "DEGRADED"

    return ReadinessReport(
        status=status,
        node_pack_count=node_pack_count,
        capability_count=capability_count,
        dependencies=deps,
    )

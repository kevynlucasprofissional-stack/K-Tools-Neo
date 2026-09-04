from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ktools_core.host import get_active_host_provider


def get_host_health(target_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Inspects host health metrics via active HostProvider."""
    path_str = str(Path(target_path).resolve()) if target_path is not None else None
    return get_active_host_provider().get_health_metrics(path_str)

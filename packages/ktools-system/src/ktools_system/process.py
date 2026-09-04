from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ktools_core.host import get_active_host_provider
from .models import CapabilityScope


def launch_process(
    command: Union[List[str], str],
    cwd: Optional[Union[str, Path]] = None,
    timeout_seconds: float = 30.0,
    env: Optional[Dict[str, str]] = None,
    scope: Optional[CapabilityScope] = None,
) -> Dict[str, Any]:
    """Safely executes a host process within optional CapabilityScope limits using the active HostProvider."""
    if scope is not None:
        scope.assert_subprocess_allowed()
        if cwd is not None:
            scope.assert_path_allowed(cwd)

    cwd_str = str(Path(cwd).resolve()) if cwd is not None else None
    return get_active_host_provider().execute_process(
        command=command,
        cwd=cwd_str,
        timeout_seconds=timeout_seconds,
        env=env,
    )

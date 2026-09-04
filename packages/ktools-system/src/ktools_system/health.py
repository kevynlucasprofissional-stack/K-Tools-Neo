from __future__ import annotations

import os
import sys
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def get_host_health(target_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Inspects local host platform, CPU, Python runtime, and disk space."""
    check_dir = str(Path(target_path).resolve()) if target_path else os.getcwd()
    
    total, used, free = 0, 0, 0
    try:
        total, used, free = shutil.disk_usage(check_dir)
    except Exception:
        pass

    percent_used = round((used / total) * 100, 2) if total > 0 else 0.0

    return {
        "platform": sys.platform,
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "disk": {
            "path": check_dir,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent_used": percent_used,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

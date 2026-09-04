from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class BrowserRuntime(Protocol):
    """Protocol defining the lifecycle contract for a managed browser runtime."""

    @property
    def name(self) -> str:
        """Name of the browser runtime (e.g. 'firefox', 'edge')."""
        ...

    def is_installed(self) -> bool:
        """Checks if the browser binary is installed and executable."""
        ...

    def get_version(self) -> str | None:
        """Returns the version string of the installed binary, or None if missing."""
        ...

    def install(self, progress_callback: Callable[[float, str], None] | None = None) -> bool:
        """Installs the browser runtime silently. Returns True on success."""
        ...

    def launch(
        self,
        profile_dir: Path | str,
        url: str | None = None,
        headless: bool = False,
        extra_args: list[str] | None = None,
    ) -> subprocess.Popen:
        """Launches the browser with an isolated profile and optional target URL."""
        ...

    def stop(self, proc: subprocess.Popen | None = None, timeout_sec: float = 5.0) -> bool:
        """Terminates a launched process gracefully, falling back to kill."""
        ...

    def health_check(self) -> dict[str, Any]:
        """Runs diagnostics on the runtime installation and returns a health status dict."""
        ...

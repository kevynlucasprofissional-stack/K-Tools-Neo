from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from .firefox import FirefoxRuntime, default_firefox_profile_dir, default_firefox_runtime_dir
from .runtime import BrowserRuntime


class BrowserRuntimeManager:
    """Orchestrates managed browser runtimes for K-Tools."""

    def __init__(
        self,
        primary_runtime: BrowserRuntime | None = None,
        default_profile_dir: Path | str | None = None,
    ):
        self._primary = primary_runtime or FirefoxRuntime()
        self._default_profile_dir = (
            Path(default_profile_dir) if default_profile_dir else default_firefox_profile_dir()
        )

    @property
    def primary(self) -> BrowserRuntime:
        return self._primary

    @property
    def profile_dir(self) -> Path:
        return self._default_profile_dir

    def is_ready(self) -> bool:
        return self._primary.is_installed()

    def ensure_runtime(self, progress_callback: Callable[[float, str], None] | None = None) -> bool:
        if self._primary.is_installed():
            return True
        return self._primary.install(progress_callback=progress_callback)

    def launch_session(
        self,
        url: str | None = None,
        profile_dir: Path | str | None = None,
        headless: bool = False,
    ):
        p_dir = Path(profile_dir) if profile_dir else self._default_profile_dir
        p_dir.mkdir(parents=True, exist_ok=True)
        if not self._primary.is_installed():
            success = self.ensure_runtime()
            if not success:
                raise RuntimeError("Não foi possível provisionar o runtime do navegador gerenciado.")
        # Apply suppression prefs if first time (FirefoxRuntime protocol)
        if hasattr(self._primary, "apply_profile_prefs"):
            if not (p_dir / "user.js").exists():
                self._primary.apply_profile_prefs(p_dir)
        return self._primary.launch(profile_dir=p_dir, url=url, headless=headless)

    def health_check(self) -> dict[str, Any]:
        return {
            "primary": self._primary.health_check(),
            "profile_dir": str(self._default_profile_dir),
            "profile_exists": self._default_profile_dir.exists(),
        }

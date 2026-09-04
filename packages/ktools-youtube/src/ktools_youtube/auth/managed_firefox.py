from __future__ import annotations

import http.cookiejar
import os
from pathlib import Path
from typing import Any

from ..browser.firefox import FirefoxRuntime, default_firefox_profile_dir
from ..browser.manager import BrowserRuntimeManager
from .base import AuthProvider, AuthState
from .bridge import inspect_cookiejar_auth


class ManagedFirefoxAuthProvider:
    """Primary & Official YouTube AuthProvider using K-Tools Managed Firefox and dedicated profile."""

    def __init__(
        self,
        profile_dir: Path | str | None = None,
        runtime: FirefoxRuntime | None = None,
        manager: BrowserRuntimeManager | None = None,
    ):
        self._profile_dir = (
            Path(profile_dir) if profile_dir else default_firefox_profile_dir()
        )
        self._runtime = runtime or (manager.primary if manager else FirefoxRuntime())
        self._manager = manager or BrowserRuntimeManager(
            primary_runtime=self._runtime,
            default_profile_dir=self._profile_dir,
        )
        self._cached_jar: http.cookiejar.CookieJar | None = None
        self._last_state: AuthState = AuthState.NOT_CONNECTED

    @property
    def name(self) -> str:
        return "managed_firefox"

    @property
    def profile_dir(self) -> Path:
        return self._profile_dir

    @property
    def runtime(self) -> FirefoxRuntime:
        return self._runtime

    def is_available(self) -> bool:
        """Available if runtime is installed or installable on this OS."""
        if self._runtime.is_installed():
            return True
        # On Windows, runtime is self-provisionable
        return os.name == "nt"

    def get_cookiejar(self) -> http.cookiejar.CookieJar | None:
        if self._cached_jar is None:
            self.refresh()
        return self._cached_jar

    def get_state(self) -> AuthState:
        if self._cached_jar is None:
            return self.refresh()
        info = inspect_cookiejar_auth(self._cached_jar)
        if info["active"]:
            return AuthState.ACTIVE
        if info["expired"]:
            return AuthState.REAUTH_REQUIRED
        return AuthState.NOT_CONNECTED

    def refresh(self) -> AuthState:
        """Extracts cookies from the dedicated profile using yt-dlp's explicit profile resolution."""
        cookies_db = self._profile_dir / "cookies.sqlite"
        if not cookies_db.exists() and not self._profile_dir.exists():
            self._cached_jar = None
            self._last_state = AuthState.NOT_CONNECTED
            return AuthState.NOT_CONNECTED

        try:
            import yt_dlp.cookies

            # yt-dlp treats profile paths containing separators as explicit directories
            jar = yt_dlp.cookies.extract_cookies_from_browser("firefox", str(self._profile_dir))
            self._cached_jar = jar

            if jar is None:
                self._last_state = AuthState.NOT_CONNECTED
                return self._last_state

            info = inspect_cookiejar_auth(jar)
            if info["active"]:
                self._last_state = AuthState.ACTIVE
            elif info["expired"]:
                self._last_state = AuthState.REAUTH_REQUIRED
            else:
                self._last_state = AuthState.NOT_CONNECTED
        except Exception:
            self._cached_jar = None
            self._last_state = AuthState.NOT_CONNECTED

        return self._last_state

    def launch_login_flow(self, url: str = "https://accounts.google.com/ServiceLogin?service=youtube") -> Any:
        """Ensures isolated runtime is installed and opens visible browser directly in login flow."""
        self._profile_dir.mkdir(parents=True, exist_ok=True)
        if not self._runtime.is_installed():
            success = self._manager.ensure_runtime()
            if not success:
                raise RuntimeError(
                    "Não foi possível baixar e instalar o Firefox Runtime isolado do K-Tools."
                )

        return self._manager.launch_session(
            url=url,
            profile_dir=self._profile_dir,
            headless=False,
        )

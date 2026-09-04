from __future__ import annotations

import http.cookiejar
from typing import Any

from .base import AuthProvider, AuthState
from .bridge import inspect_cookiejar_auth


class FirefoxAuthProvider:
    """Fallback provider using yt-dlp native extraction from Firefox."""

    def __init__(self, profile: str | None = None):
        self._profile = profile
        self._cached_jar: http.cookiejar.CookieJar | None = None
        self._last_state: AuthState = AuthState.NOT_CONNECTED

    @property
    def name(self) -> str:
        return "firefox"

    def is_available(self) -> bool:
        try:
            import yt_dlp.cookies
            jar = yt_dlp.cookies.extract_cookies_from_browser("firefox", self._profile)
            return jar is not None
        except Exception:
            return False

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
        try:
            import yt_dlp.cookies
            jar = yt_dlp.cookies.extract_cookies_from_browser("firefox", self._profile)
            self._cached_jar = jar
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

    def launch_login_flow(self) -> None:
        pass

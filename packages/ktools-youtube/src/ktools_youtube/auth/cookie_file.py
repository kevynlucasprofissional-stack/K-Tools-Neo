from __future__ import annotations

import http.cookiejar
import os
from pathlib import Path

from .base import AuthProvider, AuthState
from .bridge import inspect_cookiejar_auth


class CookieFileAuthProvider:
    """Manual fallback reading a Netscape-formatted cookies.txt file."""

    def __init__(self, cookie_file_path: Path | str | None = None):
        self._path = Path(cookie_file_path) if cookie_file_path else None
        self._cached_jar: http.cookiejar.CookieJar | None = None

    @property
    def name(self) -> str:
        return "cookie_file"

    def is_available(self) -> bool:
        return self._path is not None and self._path.is_file()

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
        if not self.is_available() or not self._path:
            self._cached_jar = None
            return AuthState.NOT_CONNECTED

        try:
            jar = http.cookiejar.MozillaCookieJar(str(self._path))
            jar.load(ignore_discard=True, ignore_expires=True)
            self._cached_jar = jar
            info = inspect_cookiejar_auth(jar)
            if info["active"]:
                return AuthState.ACTIVE
            if info["expired"]:
                return AuthState.REAUTH_REQUIRED
            return AuthState.NOT_CONNECTED
        except Exception:
            self._cached_jar = None
            return AuthState.ERROR

    def launch_login_flow(self) -> None:
        pass

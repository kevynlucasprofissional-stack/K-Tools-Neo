from __future__ import annotations

import http.cookiejar
from typing import Sequence

from .base import AuthProvider, AuthState
from .edge_cdp import EdgeCdpAuthProvider
from .firefox import FirefoxAuthProvider
from .cookie_file import CookieFileAuthProvider


class YouTubeAuthManager:
    """Manages YouTube authentication providers with fail-open fallback order."""

    def __init__(self, providers: Sequence[AuthProvider] | None = None):
        if providers is not None:
            self._providers = list(providers)
        else:
            self._providers = [
                EdgeCdpAuthProvider(),
                FirefoxAuthProvider(),
                CookieFileAuthProvider(),
            ]

    @property
    def providers(self) -> list[AuthProvider]:
        return list(self._providers)

    def active_provider(self) -> AuthProvider | None:
        # First provider that is available and in ACTIVE state
        for p in self._providers:
            if p.is_available() and p.get_state() == AuthState.ACTIVE:
                return p
        # Otherwise first available provider
        for p in self._providers:
            if p.is_available():
                return p
        return self._providers[0] if self._providers else None

    def get_state(self) -> AuthState:
        provider = self.active_provider()
        if not provider or not provider.is_available():
            return AuthState.NOT_CONNECTED
        return provider.get_state()

    def get_cookiejar(self) -> http.cookiejar.CookieJar | None:
        provider = self.active_provider()
        if not provider or not provider.is_available():
            return None
        return provider.get_cookiejar()

    def refresh(self) -> AuthState:
        provider = self.active_provider()
        if not provider or not provider.is_available():
            return AuthState.NOT_CONNECTED
        return provider.refresh()

    def launch_login(self) -> None:
        provider = self.active_provider()
        if provider:
            provider.launch_login_flow()

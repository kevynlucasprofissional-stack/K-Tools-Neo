from __future__ import annotations

import http.cookiejar
from typing import Sequence

from .base import AuthProvider, AuthState
from .cookie_file import CookieFileAuthProvider
from .edge_cdp import EdgeCdpAuthProvider
from .managed_firefox import ManagedFirefoxAuthProvider


class YouTubeAuthManager:
    """Manages YouTube authentication providers following the official priority order:
    1. Managed Firefox (Primary & Official)
    2. Microsoft Edge CDP (Fallback)
    3. Cookie File / cookies.txt (Advanced Fallback)
    """

    def __init__(self, providers: Sequence[AuthProvider] | None = None):
        if providers is not None:
            self._providers = list(providers)
        else:
            self._providers = [
                ManagedFirefoxAuthProvider(),
                EdgeCdpAuthProvider(),
                CookieFileAuthProvider(),
            ]

    @property
    def providers(self) -> list[AuthProvider]:
        return list(self._providers)

    def get_provider(self, name: str) -> AuthProvider | None:
        for p in self._providers:
            if p.name == name:
                return p
        return None

    def active_provider(self) -> AuthProvider | None:
        """Selects the active provider according to priority.
        1. First available provider with an ACTIVE authenticated session.
        2. If none active, first available provider according to priority.
        """
        # Phase 1: Search for an active session in priority order
        for p in self._providers:
            if p.is_available() and p.get_state() == AuthState.ACTIVE:
                return p

        # Phase 2: First available provider in priority order
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

    def launch_login(self, provider_name: str | None = None) -> None:
        if provider_name:
            target = self.get_provider(provider_name)
            if target:
                target.launch_login_flow()
                return
        provider = self.active_provider()
        if provider:
            provider.launch_login_flow()

    def get_all_states(self) -> dict[str, AuthState]:
        states: dict[str, AuthState] = {}
        for p in self._providers:
            if p.is_available():
                states[p.name] = p.get_state()
            else:
                states[p.name] = AuthState.NOT_CONNECTED
        return states

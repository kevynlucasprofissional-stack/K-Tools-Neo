import http.cookiejar
import unittest
from unittest.mock import MagicMock

from ktools_youtube.auth.base import AuthProvider, AuthState
from ktools_youtube.auth.manager import YouTubeAuthManager
from ktools_youtube.auth.managed_firefox import ManagedFirefoxAuthProvider
from ktools_youtube.auth.edge_cdp import EdgeCdpAuthProvider
from ktools_youtube.auth.cookie_file import CookieFileAuthProvider


class DummyProvider:
    def __init__(self, name: str, available: bool, state: AuthState, jar: http.cookiejar.CookieJar | None = None):
        self._name = name
        self._available = available
        self._state = state
        self._jar = jar

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def get_state(self) -> AuthState:
        return self._state

    def get_cookiejar(self) -> http.cookiejar.CookieJar | None:
        return self._jar

    def refresh(self) -> AuthState:
        return self._state

    def launch_login_flow(self) -> None:
        pass


class TestAuthManager(unittest.TestCase):
    def test_default_providers_priority_order(self):
        manager = YouTubeAuthManager()
        providers = manager.providers
        self.assertEqual(len(providers), 3)
        self.assertIsInstance(providers[0], ManagedFirefoxAuthProvider)
        self.assertIsInstance(providers[1], EdgeCdpAuthProvider)
        self.assertIsInstance(providers[2], CookieFileAuthProvider)

    def test_prefers_active_provider_respecting_priority(self):
        p_firefox = DummyProvider("managed_firefox", available=True, state=AuthState.ACTIVE, jar=http.cookiejar.CookieJar())
        p_edge = DummyProvider("edge_cdp", available=True, state=AuthState.ACTIVE, jar=http.cookiejar.CookieJar())
        manager = YouTubeAuthManager(providers=[p_firefox, p_edge])

        self.assertEqual(manager.active_provider().name, "managed_firefox")

    def test_falls_back_to_edge_when_firefox_inactive_and_edge_active(self):
        p_firefox = DummyProvider("managed_firefox", available=True, state=AuthState.NOT_CONNECTED)
        p_edge = DummyProvider("edge_cdp", available=True, state=AuthState.ACTIVE, jar=http.cookiejar.CookieJar())
        manager = YouTubeAuthManager(providers=[p_firefox, p_edge])

        self.assertEqual(manager.active_provider().name, "edge_cdp")
        self.assertEqual(manager.get_state(), AuthState.ACTIVE)

    def test_falls_back_to_cookiefile_when_browsers_inactive(self):
        p_firefox = DummyProvider("managed_firefox", available=True, state=AuthState.NOT_CONNECTED)
        p_edge = DummyProvider("edge_cdp", available=True, state=AuthState.NOT_CONNECTED)
        p_cookie = DummyProvider("cookie_file", available=True, state=AuthState.ACTIVE, jar=http.cookiejar.CookieJar())
        manager = YouTubeAuthManager(providers=[p_firefox, p_edge, p_cookie])

        self.assertEqual(manager.active_provider().name, "cookie_file")
        self.assertEqual(manager.get_state(), AuthState.ACTIVE)

    def test_falls_back_to_first_available_when_none_active(self):
        p1 = DummyProvider("managed_firefox", available=False, state=AuthState.NOT_CONNECTED)
        p2 = DummyProvider("edge_cdp", available=True, state=AuthState.NOT_CONNECTED)
        manager = YouTubeAuthManager(providers=[p1, p2])

        self.assertEqual(manager.active_provider().name, "edge_cdp")
        self.assertEqual(manager.get_state(), AuthState.NOT_CONNECTED)

    def test_reauth_required_state(self):
        p1 = DummyProvider("managed_firefox", available=True, state=AuthState.REAUTH_REQUIRED)
        manager = YouTubeAuthManager(providers=[p1])

        self.assertEqual(manager.get_state(), AuthState.REAUTH_REQUIRED)

    def test_get_all_states(self):
        p1 = DummyProvider("managed_firefox", available=True, state=AuthState.ACTIVE)
        p2 = DummyProvider("edge_cdp", available=True, state=AuthState.NOT_CONNECTED)
        p3 = DummyProvider("cookie_file", available=False, state=AuthState.NOT_CONNECTED)
        manager = YouTubeAuthManager(providers=[p1, p2, p3])

        states = manager.get_all_states()
        self.assertEqual(states["managed_firefox"], AuthState.ACTIVE)
        self.assertEqual(states["edge_cdp"], AuthState.NOT_CONNECTED)
        self.assertEqual(states["cookie_file"], AuthState.NOT_CONNECTED)


if __name__ == "__main__":
    unittest.main()

import http.cookiejar
import unittest
from unittest.mock import MagicMock

from ktools_youtube.auth.base import AuthProvider, AuthState
from ktools_youtube.auth.manager import YouTubeAuthManager


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
    def test_prefers_active_provider(self):
        p1 = DummyProvider("edge_cdp", available=True, state=AuthState.NOT_CONNECTED)
        p2 = DummyProvider("firefox", available=True, state=AuthState.ACTIVE, jar=http.cookiejar.CookieJar())
        manager = YouTubeAuthManager(providers=[p1, p2])

        self.assertEqual(manager.active_provider().name, "firefox")
        self.assertEqual(manager.get_state(), AuthState.ACTIVE)
        self.assertIsNotNone(manager.get_cookiejar())

    def test_falls_back_to_first_available_when_none_active(self):
        p1 = DummyProvider("edge_cdp", available=True, state=AuthState.NOT_CONNECTED)
        p2 = DummyProvider("firefox", available=False, state=AuthState.NOT_CONNECTED)
        manager = YouTubeAuthManager(providers=[p1, p2])

        self.assertEqual(manager.active_provider().name, "edge_cdp")
        self.assertEqual(manager.get_state(), AuthState.NOT_CONNECTED)

    def test_reauth_required_state(self):
        p1 = DummyProvider("edge_cdp", available=True, state=AuthState.REAUTH_REQUIRED)
        manager = YouTubeAuthManager(providers=[p1])

        self.assertEqual(manager.get_state(), AuthState.REAUTH_REQUIRED)


if __name__ == "__main__":
    unittest.main()

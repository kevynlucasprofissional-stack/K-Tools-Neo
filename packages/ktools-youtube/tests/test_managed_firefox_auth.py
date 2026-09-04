import http.cookiejar
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ktools_youtube.auth.base import AuthState
from ktools_youtube.auth.managed_firefox import ManagedFirefoxAuthProvider


class TestManagedFirefoxAuthProvider(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.profile_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_provider_name_and_paths(self):
        provider = ManagedFirefoxAuthProvider(profile_dir=self.profile_dir)
        self.assertEqual(provider.name, "managed_firefox")
        self.assertEqual(provider.profile_dir, self.profile_dir)

    def test_availability_with_installed_runtime(self):
        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        provider = ManagedFirefoxAuthProvider(profile_dir=self.profile_dir, runtime=mock_rt)
        self.assertTrue(provider.is_available())

    def test_not_connected_when_profile_empty(self):
        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        provider = ManagedFirefoxAuthProvider(profile_dir=self.profile_dir, runtime=mock_rt)

        state = provider.get_state()
        self.assertEqual(state, AuthState.NOT_CONNECTED)
        self.assertIsNone(provider.get_cookiejar())

    @patch("yt_dlp.cookies.extract_cookies_from_browser")
    def test_active_state_when_valid_youtube_cookies_present(self, mock_extract):
        jar = http.cookiejar.CookieJar()
        c = http.cookiejar.Cookie(
            version=0,
            name="__Secure-3PAPISID",
            value="valid_token_xyz",
            port=None,
            port_specified=False,
            domain=".youtube.com",
            domain_specified=True,
            domain_initial_dot=True,
            path="/",
            path_specified=True,
            secure=True,
            expires=int(time.time() + 86400 * 30),
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
        )
        jar.set_cookie(c)
        mock_extract.return_value = jar

        # Create dummy cookies.sqlite to simulate presence
        (self.profile_dir / "cookies.sqlite").touch()

        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        provider = ManagedFirefoxAuthProvider(profile_dir=self.profile_dir, runtime=mock_rt)

        state = provider.get_state()
        self.assertEqual(state, AuthState.ACTIVE)
        self.assertIsNotNone(provider.get_cookiejar())

    @patch("yt_dlp.cookies.extract_cookies_from_browser")
    def test_reauth_required_when_cookies_expired(self, mock_extract):
        jar = http.cookiejar.CookieJar()
        c = http.cookiejar.Cookie(
            version=0,
            name="__Secure-3PAPISID",
            value="expired_token_xyz",
            port=None,
            port_specified=False,
            domain=".youtube.com",
            domain_specified=True,
            domain_initial_dot=True,
            path="/",
            path_specified=True,
            secure=True,
            expires=int(time.time() - 3600),  # expired 1 hour ago
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
        )
        jar.set_cookie(c)
        mock_extract.return_value = jar

        (self.profile_dir / "cookies.sqlite").touch()

        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        provider = ManagedFirefoxAuthProvider(profile_dir=self.profile_dir, runtime=mock_rt)

        state = provider.get_state()
        self.assertEqual(state, AuthState.REAUTH_REQUIRED)

    def test_launch_login_flow_triggers_runtime(self):
        mock_mgr = MagicMock()
        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        mock_mgr.primary = mock_rt

        provider = ManagedFirefoxAuthProvider(
            profile_dir=self.profile_dir,
            runtime=mock_rt,
            manager=mock_mgr,
        )

        provider.launch_login_flow()
        mock_mgr.launch_session.assert_called_once()
        args, kwargs = mock_mgr.launch_session.call_args
        self.assertIn("accounts.google.com", kwargs.get("url") or args[0] if args else kwargs.get("url"))
        self.assertEqual(kwargs.get("profile_dir"), self.profile_dir)
        self.assertFalse(kwargs.get("headless"))


if __name__ == "__main__":
    unittest.main()

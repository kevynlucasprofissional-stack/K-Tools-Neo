import http.cookiejar
import time
import unittest

from ktools_youtube.auth.bridge import (
    is_domain_allowed,
    cdp_cookies_to_cookiejar,
    inspect_cookiejar_auth,
    cookiejar_to_netscape_text,
)


class TestCookieBridge(unittest.TestCase):
    def test_domain_filtering(self):
        self.assertTrue(is_domain_allowed(".youtube.com"))
        self.assertTrue(is_domain_allowed("youtube.com"))
        self.assertTrue(is_domain_allowed(".google.com"))
        self.assertTrue(is_domain_allowed("accounts.google.com"))
        self.assertFalse(is_domain_allowed("evil.com"))
        self.assertFalse(is_domain_allowed("facebook.com"))
        self.assertFalse(is_domain_allowed(".notyoutube.com"))

    def test_cdp_cookies_to_cookiejar(self):
        raw_cdp = [
            {
                "name": "LOGIN_INFO",
                "value": "token_abc123",
                "domain": ".youtube.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "expires": time.time() + 3600,
            },
            {
                "name": "TRACKING",
                "value": "secret",
                "domain": ".untrusted-site.com",
                "path": "/",
            },
        ]
        jar, count = cdp_cookies_to_cookiejar(raw_cdp)
        self.assertEqual(count, 1)
        cookies = list(jar)
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0].name, "LOGIN_INFO")
        self.assertEqual(cookies[0].value, "token_abc123")
        self.assertEqual(cookies[0].domain, ".youtube.com")
        self.assertTrue(cookies[0].secure)

    def test_inspect_cookiejar_auth_active_and_expired(self):
        jar_active = http.cookiejar.CookieJar()
        jar_active.set_cookie(
            http.cookiejar.Cookie(
                0, "LOGIN_INFO", "tok", None, False, ".youtube.com", True, True, "/", True, True, time.time() + 3600, False, None, None, {}
            )
        )
        info_active = inspect_cookiejar_auth(jar_active)
        self.assertTrue(info_active["has_auth"])
        self.assertTrue(info_active["active"])
        self.assertFalse(info_active["expired"])

        jar_expired = http.cookiejar.CookieJar()
        jar_expired.set_cookie(
            http.cookiejar.Cookie(
                0, "LOGIN_INFO", "tok", None, False, ".youtube.com", True, True, "/", True, True, time.time() - 3600, False, None, None, {}
            )
        )
        info_expired = inspect_cookiejar_auth(jar_expired)
        self.assertTrue(info_expired["has_auth"])
        self.assertFalse(info_expired["active"])
        self.assertTrue(info_expired["expired"])

    def test_cookiejar_to_netscape_text(self):
        jar = http.cookiejar.CookieJar()
        jar.set_cookie(
            http.cookiejar.Cookie(
                0, "SID", "secret_val", None, False, ".youtube.com", True, True, "/", True, True, 2000000000, False, None, None, {}
            )
        )
        text = cookiejar_to_netscape_text(jar)
        self.assertIn("# Netscape HTTP Cookie File", text)
        self.assertIn(".youtube.com\tTRUE\t/\tTRUE\t2000000000\tSID\tsecret_val", text)


if __name__ == "__main__":
    unittest.main()

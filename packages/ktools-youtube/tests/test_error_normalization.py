import unittest

from ktools_youtube.engine.errors import (
    AgeRestrictedError,
    AuthRequiredError,
    FFmpegRequiredError,
    GeoBlockedError,
    NetworkError,
    PlaylistUnavailableError,
    PoTokenRequiredError,
    PrivateVideoError,
    VideoUnavailableError,
    YouTubeError,
    normalize_ytdlp_error,
)


class TestErrorNormalization(unittest.TestCase):
    def test_age_restricted(self):
        err = normalize_ytdlp_error(Exception("ERROR: Sign in to confirm your age. This video may be inappropriate."))
        self.assertIsInstance(err, AgeRestrictedError)
        self.assertEqual(err.code, "AGE_RESTRICTED")

    def test_bot_po_token(self):
        err = normalize_ytdlp_error(Exception("ERROR: Sign in to confirm you're not a bot. Use --cookies or SABR."))
        self.assertIsInstance(err, PoTokenRequiredError)
        self.assertEqual(err.code, "PO_TOKEN_REQUIRED")

    def test_private_video(self):
        err = normalize_ytdlp_error(Exception("ERROR: Private video. Sign in if you've been granted access."))
        self.assertIsInstance(err, PrivateVideoError)
        self.assertEqual(err.code, "PRIVATE_VIDEO")

    def test_login_required(self):
        err = normalize_ytdlp_error(Exception("ERROR: This video is only available to channel members."))
        self.assertIsInstance(err, AuthRequiredError)
        self.assertEqual(err.code, "AUTH_REQUIRED")

    def test_network_error(self):
        err = normalize_ytdlp_error(Exception("URLError: <urlopen error [Errno 11001] getaddrinfo failed>"))
        self.assertIsInstance(err, NetworkError)
        self.assertEqual(err.code, "NETWORK_ERROR")

    def test_generic_fallback(self):
        err = normalize_ytdlp_error(Exception("Unexpected failure 42"))
        self.assertIsInstance(err, YouTubeError)
        self.assertEqual(err.code, "YTDLP_ERROR")


if __name__ == "__main__":
    unittest.main()

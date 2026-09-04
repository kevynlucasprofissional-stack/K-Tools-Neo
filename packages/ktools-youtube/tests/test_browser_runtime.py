import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ktools_youtube.browser.firefox import (
    FirefoxRuntime,
    default_firefox_profile_dir,
    default_firefox_runtime_dir,
)
from ktools_youtube.browser.manager import BrowserRuntimeManager


class TestFirefoxRuntime(unittest.TestCase):
    def test_default_paths(self):
        runtime_dir = default_firefox_runtime_dir()
        profile_dir = default_firefox_profile_dir()

        self.assertIn("K-Tools-Neo", str(runtime_dir))
        self.assertIn("runtimes", str(runtime_dir))
        self.assertIn("browser-profiles", str(profile_dir))
        self.assertIn("youtube", str(profile_dir))

    def test_runtime_properties(self):
        custom_dir = Path("/tmp/custom_firefox")
        rt = FirefoxRuntime(install_dir=custom_dir)

        self.assertEqual(rt.name, "firefox")
        self.assertEqual(rt.install_dir, custom_dir)
        self.assertEqual(rt.executable_path, custom_dir / ("firefox.exe" if os.name == "nt" else "firefox"))

    @patch("ktools_youtube.browser.firefox.subprocess.run")
    def test_get_version_installed(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Mozilla Firefox 135.0\n", returncode=0)
        rt = FirefoxRuntime(install_dir=Path("/mock/firefox"))

        with patch.object(rt, "is_installed", return_value=True):
            ver = rt.get_version()
            self.assertEqual(ver, "Mozilla Firefox 135.0")

    def test_health_check_uninstalled(self):
        rt = FirefoxRuntime(install_dir=Path("/non_existent_dir_12345"))
        health = rt.health_check()

        self.assertEqual(health["name"], "firefox")
        self.assertFalse(health["installed"])
        self.assertFalse(health["healthy"])
        self.assertIsNone(health["version"])

    @patch("ktools_youtube.browser.firefox.subprocess.Popen")
    def test_launch_with_isolated_profile(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        profile = Path("/tmp/test_profile")
        rt = FirefoxRuntime(install_dir=Path("/mock/firefox"))

        with patch.object(rt, "is_installed", return_value=True):
            proc = rt.launch(profile_dir=profile, url="https://youtube.com", headless=True)
            self.assertEqual(proc, mock_proc)
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            self.assertIn("-no-remote", args)
            self.assertIn("-profile", args)
            self.assertIn(str(profile.resolve()), args)
            self.assertIn("-headless", args)
            self.assertIn("https://youtube.com", args)

    def test_stop_process(self):
        rt = FirefoxRuntime()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None

        stopped = rt.stop(mock_proc)
        self.assertTrue(stopped)
        mock_proc.terminate.assert_called_once()


class TestBrowserRuntimeManager(unittest.TestCase):
    def test_manager_delegation(self):
        mock_rt = MagicMock()
        mock_rt.is_installed.return_value = True
        mock_rt.health_check.return_value = {"installed": True, "healthy": True}

        profile = Path("/tmp/mock_prof")
        mgr = BrowserRuntimeManager(primary_runtime=mock_rt, default_profile_dir=profile)

        self.assertTrue(mgr.is_ready())
        self.assertEqual(mgr.profile_dir, profile)
        health = mgr.health_check()
        self.assertTrue(health["primary"]["healthy"])


if __name__ == "__main__":
    unittest.main()

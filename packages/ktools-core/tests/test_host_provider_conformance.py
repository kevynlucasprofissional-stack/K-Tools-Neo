import unittest
import sys
from ktools_core.host.provider import (
    HostPlatform,
    HostCapability,
    HostCapabilityUnsupportedError,
    HostProvider,
    get_active_host_provider,
    set_active_host_provider,
)
from ktools_core.host.windows import WindowsHostProvider
from ktools_core.host.linux import LinuxHostProvider


class HostProviderConformanceTests(unittest.TestCase):
    def tearDown(self):
        set_active_host_provider(None)

    def test_active_provider_detection(self):
        provider = get_active_host_provider()
        self.assertIsInstance(provider, HostProvider)
        if sys.platform == "win32":
            self.assertEqual(provider.platform, HostPlatform.WINDOWS)
            self.assertIsInstance(provider, WindowsHostProvider)

    def test_windows_provider_conformance(self):
        win_provider = WindowsHostProvider()
        self.assertEqual(win_provider.platform, HostPlatform.WINDOWS)
        self.assertTrue(win_provider.is_capability_supported(HostCapability.PROCESS_LAUNCH))
        self.assertTrue(win_provider.is_capability_supported(HostCapability.CLIPBOARD_SYNC))
        self.assertTrue(win_provider.is_capability_supported(HostCapability.HOST_HEALTH))
        self.assertTrue(win_provider.is_capability_supported(HostCapability.NOTIFICATIONS))

        # Health
        health = win_provider.get_health_metrics()
        self.assertIn("platform", health)
        self.assertIn("cpu_count", health)
        self.assertIn("disk", health)

        # Process execution
        res = win_provider.execute_process([sys.executable, "-c", "print('win-exec-ok')"])
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("win-exec-ok", res["stdout"])

        # Clipboard
        test_txt = "win-clip-verify"
        win_provider.write_clipboard(test_txt)
        self.assertEqual(win_provider.read_clipboard(), test_txt)

        # Notification
        ok = win_provider.send_notification("Title", "Message", "info")
        self.assertTrue(ok)

    def test_linux_reference_provider_conformance(self):
        linux_provider = LinuxHostProvider()
        self.assertEqual(linux_provider.platform, HostPlatform.LINUX)
        self.assertTrue(linux_provider.is_capability_supported(HostCapability.PROCESS_LAUNCH))
        self.assertTrue(linux_provider.is_capability_supported(HostCapability.CLIPBOARD_SYNC))
        self.assertTrue(linux_provider.is_capability_supported(HostCapability.HOST_HEALTH))
        self.assertTrue(linux_provider.is_capability_supported(HostCapability.NOTIFICATIONS))

        # Health
        health = linux_provider.get_health_metrics()
        self.assertIn("platform", health)
        self.assertIn("cpu_count", health)
        self.assertIn("disk", health)

        # Process execution
        res = linux_provider.execute_process([sys.executable, "-c", "print('linux-exec-ok')"])
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("linux-exec-ok", res["stdout"])

        # Clipboard
        test_txt = "linux-clip-verify"
        linux_provider.write_clipboard(test_txt)
        self.assertEqual(linux_provider.read_clipboard(), test_txt)

        # Notification
        ok = linux_provider.send_notification("Title", "Message", "info")
        self.assertTrue(ok)

    def test_unsupported_capability_rejection(self):
        class MinimalProvider(HostProvider):
            @property
            def platform(self) -> HostPlatform:
                return HostPlatform.UNKNOWN

            @property
            def name(self) -> str:
                return "Minimal"

            def supported_capabilities(self) -> tuple[HostCapability, ...]:
                return (HostCapability.HOST_HEALTH,)

            def get_health_metrics(self, target_path=None):
                return {"platform": "minimal", "cpu_count": 1, "disk": {}}

            def execute_process(self, command, cwd=None, timeout_seconds=30.0, env=None):
                raise HostCapabilityUnsupportedError("execute_process is not supported on MinimalProvider")

            def read_clipboard(self):
                raise HostCapabilityUnsupportedError("read_clipboard is not supported on MinimalProvider")

            def write_clipboard(self, text: str):
                raise HostCapabilityUnsupportedError("write_clipboard is not supported on MinimalProvider")

            def send_notification(self, title: str, message: str, level: str = "info") -> bool:
                raise HostCapabilityUnsupportedError("send_notification is not supported on MinimalProvider")

        provider = MinimalProvider()
        self.assertFalse(provider.is_capability_supported(HostCapability.PROCESS_LAUNCH))
        with self.assertRaises(HostCapabilityUnsupportedError):
            provider.execute_process(["ls"])


if __name__ == "__main__":
    unittest.main()

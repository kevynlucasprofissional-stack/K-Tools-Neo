import unittest
import sys
from ktools_core.registry import NodeRegistry
from ktools_core.invoker import CapabilityInvoker
from ktools_system.node import register_nodes
from ktools_system.models import CapabilityScope


class SystemCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()
        register_nodes(self.registry)
        self.invoker = CapabilityInvoker(self.registry)

    def test_system_process_launch_echo(self):
        # Run python -c "print('hello from subprocess')"
        cmd = [sys.executable, "-c", "print('hello from subprocess')"]
        receipt = self.invoker.invoke(
            "system.process_launch",
            inputs={"command": cmd, "timeout_seconds": 10},
        )
        self.assertEqual(receipt.status.value, "SUCCESS")
        self.assertEqual(receipt.outputs["exit_code"], 0)
        self.assertIn("hello from subprocess", receipt.outputs["stdout"])

    def test_system_host_health(self):
        receipt = self.invoker.invoke("system.host_health", inputs={})
        self.assertEqual(receipt.status.value, "SUCCESS")
        self.assertIn("platform", receipt.outputs)
        self.assertIn("python_version", receipt.outputs)
        self.assertIn("cpu_count", receipt.outputs)

    def test_system_clipboard_read_write(self):
        # Set clipboard and read back
        test_text = "ktools-clipboard-verification-token"
        w_receipt = self.invoker.invoke("system.clipboard_write", inputs={"text": test_text})
        self.assertEqual(w_receipt.status.value, "SUCCESS")

        r_receipt = self.invoker.invoke("system.clipboard_read", inputs={})
        self.assertEqual(r_receipt.status.value, "SUCCESS")
        self.assertEqual(r_receipt.outputs["text"], test_text)

    def test_system_notify_and_events(self):
        from ktools_system.events import get_system_event_stream
        stream = get_system_event_stream()
        received_events = []
        unsub = stream.subscribe(lambda e: received_events.append(e))

        receipt = self.invoker.invoke(
            "system.notify",
            inputs={"title": "Test Title", "message": "Test Message", "level": "warning"},
        )
        self.assertEqual(receipt.status.value, "SUCCESS")
        self.assertTrue(receipt.outputs["delivered"])
        self.assertTrue(receipt.outputs["event_id"].startswith("sysevt_"))

        self.assertGreaterEqual(len(received_events), 1)
        self.assertEqual(received_events[-1].event_type, "notification.warning")
        self.assertIn("Test Title", received_events[-1].message)

        unsub()

    def test_process_launch_scope_denial(self):
        from ktools_system.process import launch_process
        from ktools_system.models import ScopeViolationError

        scope = CapabilityScope(allow_subprocess=False)
        with self.assertRaises(ScopeViolationError):
            launch_process(["echo", "blocked"], scope=scope)


if __name__ == "__main__":
    unittest.main()


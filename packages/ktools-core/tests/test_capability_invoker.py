import unittest
import tempfile
from pathlib import Path

from ktools_core.registry import NodeRegistry
from ktools_core.models import NodeDefinition, PortDefinition, DataType
from ktools_core.receipt import ExecutionReceipt, ReceiptStatus
from ktools_core.invoker import CapabilityInvoker
from ktools_core.journal import MemoryRunJournal
from ktools_core.diagnostics import DiagnosticsSession


class CapabilityInvokerTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.journal = MemoryRunJournal()
        self.diagnostics = DiagnosticsSession(str(Path(self.temp_dir.name) / "diag"))
        self.invoker = CapabilityInvoker(
            registry=self.registry,
            journal=self.journal,
            diagnostics=self.diagnostics,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_invoke_successful_capability_emits_receipt(self):
        def echo_handler(inputs, config, context):
            return {"greeting": f"Hello, {inputs['name']}!"}

        self.registry.register(
            NodeDefinition(
                type_id="test.echo",
                title="Echo",
                category="Testing",
                inputs={"name": PortDefinition(DataType.TEXT, required=True)},
                outputs={"greeting": PortDefinition(DataType.TEXT)},
            ),
            echo_handler,
        )

        receipt = self.invoker.invoke("test.echo", inputs={"name": "K-Tools"})
        self.assertIsInstance(receipt, ExecutionReceipt)
        self.assertEqual(receipt.status, ReceiptStatus.SUCCESS)
        self.assertEqual(receipt.capability_id, "test.echo")
        self.assertEqual(receipt.outputs["greeting"], "Hello, K-Tools!")
        self.assertGreaterEqual(receipt.duration_seconds, 0.0)
        self.assertTrue(receipt.receipt_id)
        self.assertGreater(len(self.journal.events), 0)

    def test_invoke_missing_required_input_fails_with_receipt(self):
        def dummy_handler(inputs, config, context):
            return {"res": 42}

        self.registry.register(
            NodeDefinition(
                type_id="test.strict",
                title="Strict",
                category="Testing",
                inputs={"required_val": PortDefinition(DataType.NUMBER, required=True)},
                outputs={"res": PortDefinition(DataType.NUMBER)},
            ),
            dummy_handler,
        )

        receipt = self.invoker.invoke("test.strict", inputs={})
        self.assertEqual(receipt.status, ReceiptStatus.FAILED)
        self.assertIn("required_val", receipt.error["message"])

    def test_invoke_unknown_capability_fails_cleanly(self):
        receipt = self.invoker.invoke("unknown.capability", inputs={})
        self.assertEqual(receipt.status, ReceiptStatus.FAILED)
        self.assertIn("unknown.capability", receipt.error["message"])


if __name__ == "__main__":
    unittest.main()

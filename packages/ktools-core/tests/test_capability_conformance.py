import unittest
import json
import io
from contextlib import redirect_stdout

from ktools_core.registry import NodeRegistry, load_all_installed_node_packs
from ktools_core.manifest import generate_capability_manifest
from ktools_core.invoker import CapabilityInvoker
from ktools_core.mcp_server import KToolsMCPServer
from ktools_core.cli import main
from ktools_core.engine import WorkflowEngine
from ktools_core.models import WorkflowDefinition, WorkflowNode, WorkflowEdge


class CapabilityConformanceTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_all_installed_node_packs()
        self.invoker = CapabilityInvoker(self.registry)
        self.mcp = KToolsMCPServer(self.registry, self.invoker)

    def test_all_34_capabilities_registered_and_in_manifest(self):
        manifest = generate_capability_manifest(self.registry)
        self.assertGreaterEqual(len(manifest.capabilities), 34)
        for cap_id in (
            "core.identity",
            "media.convert_lossless_alac",
            "media.merge_audio_studio",
            "media.deess_audio",
            "filesystem.drive_stream_scan",
            "filesystem.structure_report",
            "text.tldv_extract",
            "system.host_health",
            "system.process_launch",
            "system.notify",
            "script.python_run",
            "youtube.download",
        ):
            self.assertIn(cap_id, manifest.capabilities)

    def test_direct_invoker_mcp_and_cli_parity_on_identity(self):
        test_val = "K-Tools Conformance Value"

        # 1. Direct API
        direct_receipt = self.invoker.invoke("core.identity", inputs={"value": test_val})
        self.assertEqual(direct_receipt.status.value, "SUCCESS")
        self.assertEqual(direct_receipt.outputs["value"], test_val)

        # 2. MCP Server
        mcp_res = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {"name": "core_identity", "arguments": {"value": test_val}},
        })
        mcp_text = mcp_res["result"]["content"][0]["text"]
        mcp_receipt = json.loads(mcp_text)
        self.assertEqual(mcp_receipt["status"], "SUCCESS")
        self.assertEqual(mcp_receipt["outputs"]["value"], test_val)

        # 3. CLI
        out_buf = io.StringIO()
        with redirect_stdout(out_buf):
            code = main(["capabilities", "invoke", "core.identity", "--input", f"value={test_val}"])
        self.assertEqual(code, 0)
        cli_receipt = json.loads(out_buf.getvalue())
        self.assertEqual(cli_receipt["status"], "SUCCESS")
        self.assertEqual(cli_receipt["outputs"]["value"], test_val)

        # 4. WorkflowEngine
        wf = WorkflowDefinition(
            id="wf_conformance",
            nodes=(
                WorkflowNode(id="n0", type="text.literal", config={"value": test_val}),
                WorkflowNode(id="n1", type="core.identity"),
            ),
            edges=(
                WorkflowEdge(source_node="n0", source_port="text", target_node="n1", target_port="value"),
            ),
        )
        engine = WorkflowEngine(self.registry)
        wf_result = engine.execute(wf)
        self.assertEqual(wf_result.node_outputs["n1"]["value"], test_val)


if __name__ == "__main__":
    unittest.main()

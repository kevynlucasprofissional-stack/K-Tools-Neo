import unittest
import json
from ktools_core.registry import NodeRegistry
from ktools_core.models import NodeDefinition, PortDefinition, DataType
from ktools_core.mcp_server import KToolsMCPServer


class CapabilityMCPTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()
        self.mcp = KToolsMCPServer(self.registry)

    def test_mcp_tools_list(self):
        self.registry.register(
            NodeDefinition(
                type_id="text.concat_sample",
                title="Concat Sample",
                category="Text",
                inputs={"a": PortDefinition(DataType.TEXT, required=True)},
                outputs={"res": PortDefinition(DataType.TEXT)},
            ),
            lambda inp, cfg, ctx: {"res": inp["a"]},
        )

        response = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })

        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "text_concat_sample")
        self.assertIn("a", tools[0]["inputSchema"]["properties"])

    def test_mcp_tools_call(self):
        self.registry.register(
            NodeDefinition(
                type_id="math.add",
                title="Add",
                category="Math",
                inputs={
                    "x": PortDefinition(DataType.NUMBER, required=True),
                    "y": PortDefinition(DataType.NUMBER, required=True),
                },
                outputs={"sum": PortDefinition(DataType.NUMBER)},
            ),
            lambda inp, cfg, ctx: {"sum": inp["x"] + inp["y"]},
        )

        response = self.mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "math_add",
                "arguments": {"x": 10, "y": 32},
            },
        })

        self.assertEqual(response["id"], 2)
        content = response["result"]["content"]
        self.assertEqual(content[0]["type"], "text")
        parsed = json.loads(content[0]["text"])
        self.assertEqual(parsed["status"], "SUCCESS")
        self.assertEqual(parsed["outputs"]["sum"], 42)


if __name__ == "__main__":
    unittest.main()

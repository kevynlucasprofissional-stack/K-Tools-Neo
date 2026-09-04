import unittest
from ktools_core.registry import NodeRegistry
from ktools_core.invoker import CapabilityInvoker
from ktools_core.engine import WorkflowEngine
from ktools_core.models import WorkflowDefinition, WorkflowNode, WorkflowEdge
from ktools_script.node import register_nodes


class ScriptNodeTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()
        register_nodes(self.registry)
        self.invoker = CapabilityInvoker(self.registry)

    def test_direct_invoker_script_execution(self):
        code = "result = f'K-Tools: {data}'; outputs['result'] = result"
        receipt = self.invoker.invoke(
            "script.python_run",
            inputs={"code": code, "data": "Processamento customizado"},
        )
        self.assertEqual(receipt.status.value, "SUCCESS")
        self.assertEqual(receipt.outputs["result"], "K-Tools: Processamento customizado")
        self.assertEqual(receipt.outputs["exit_code"], 0)

    def test_workflow_engine_script_integration(self):
        wf = WorkflowDefinition(
            id="script_wf",
            nodes=(
                WorkflowNode(
                    id="py_node",
                    type="script.python_run",
                    config={
                        "code": "result = [x.upper() for x in ['take1', 'take2']]; outputs['result'] = result"
                    },
                ),
            ),
            edges=(),
        )
        engine = WorkflowEngine(self.registry)
        res = engine.execute(wf)
        self.assertEqual(res.node_outputs["py_node"]["result"], ["TAKE1", "TAKE2"])


if __name__ == "__main__":
    unittest.main()

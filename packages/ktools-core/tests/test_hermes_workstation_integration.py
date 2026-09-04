import unittest
from ktools_core.registry import load_all_installed_node_packs, NodeRegistry
from ktools_core.invoker import CapabilityInvoker
from ktools_core.models import (
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    DataType,
    PortDefinition,
    NodeDefinition,
    CachePolicy,
)
from ktools_core.adapters.hermes import HermesCapabilityAdapter
from ktools_core.adapters.workflow_capability import register_workflow_as_capability
from ktools_core.readiness import check_readiness


class HermesWorkstationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_all_installed_node_packs()
        self.invoker = CapabilityInvoker(self.registry)
        self.adapter = HermesCapabilityAdapter(self.registry, self.invoker)

    def test_hermes_capability_invocation(self):
        req = {
            "action": "core.identity",
            "parameters": {"value": "hermes-sync-test"},
            "session_id": "hermes-session-42",
        }
        res = self.adapter.dispatch(req)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["outputs"]["value"], "hermes-sync-test")
        self.assertIn("receipt_id", res)
        self.assertIn("duration_ms", res)

    def test_hermes_policy_handshake_scope_denial(self):
        req = {
            "action": "system.process_launch",
            "parameters": {"command": ["python", "-c", "print(1)"]},
            "caller_scope": {"allow_subprocess": False},
        }
        res = self.adapter.dispatch(req)
        self.assertEqual(res["status"], "DENIED")
        self.assertIn("denied by CapabilityScope", res["error"])

    def test_hermes_policy_handshake_requires_confirmation(self):
        # Register a mock destructive capability
        self.registry.register(
            NodeDefinition(
                type_id="mock.destructive_format",
                title="Mock Format",
                category="Mock",
                inputs={},
                outputs={"done": PortDefinition(DataType.BOOLEAN)},
                version="1",
                cache_policy=CachePolicy.NEVER,
            ),
            lambda inputs, config, ctx: {"done": True},
        )

        req_unconfirmed = {
            "action": "mock.destructive_format",
            "parameters": {},
            "caller_scope": {"allow_destructive": False},
            "side_effect_class": "destructive_mutation",
            "human_confirmed": False,
        }
        res = self.adapter.dispatch(req_unconfirmed)
        self.assertEqual(res["status"], "REQUIRES_CONFIRMATION")
        self.assertEqual(res["policy_action"], "require_human_confirmation")

        # Now dispatch with human_confirmed = True
        req_confirmed = {
            "action": "mock.destructive_format",
            "parameters": {},
            "caller_scope": {"allow_destructive": False},
            "side_effect_class": "destructive_mutation",
            "human_confirmed": True,
        }
        res2 = self.adapter.dispatch(req_confirmed)
        self.assertEqual(res2["status"], "SUCCESS")
        self.assertTrue(res2["outputs"]["done"])

    def test_workflow_as_capability(self):
        # Define a 2-node workflow DAG: n1: identity -> n2: identity
        wf = WorkflowDefinition(
            id="test_wf_identity",
            nodes=(
                WorkflowNode(id="n1", type="core.identity"),
                WorkflowNode(id="n2", type="core.identity"),
            ),
            edges=(
                WorkflowEdge(source_node="n1", source_port="value", target_node="n2", target_port="value"),
            ),
        )

        cap_id = "workflow.double_identity"
        register_workflow_as_capability(
            registry=self.registry,
            workflow_def=wf,
            capability_id=cap_id,
            title="Double Identity Pipeline",
            input_mapping={"text_in": ("n1", "value")},
            output_mapping={"text_out": ("n2", "value")},
        )

        # Ensure registered in registry
        self.assertIn(cap_id, self.registry.type_ids())

        # Invoke through Hermes adapter as a single atomic capability
        res = self.adapter.dispatch({
            "action": cap_id,
            "parameters": {"text_in": "pipeline-stream-data"},
        })
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["outputs"]["text_out"], "pipeline-stream-data")

    def test_readiness_check(self):
        report = check_readiness(self.registry)
        self.assertIn(report.status, ("READY", "DEGRADED"))
        self.assertGreaterEqual(report.node_pack_count, 4)
        self.assertGreaterEqual(report.capability_count, 20)
        self.assertIsInstance(report.dependencies, dict)
        self.assertIn("python", report.dependencies)


if __name__ == "__main__":
    unittest.main()

import unittest
from ktools_core.registry import NodeRegistry
from ktools_core.manifest import (
    SideEffectClass,
    CapabilityDefinition,
    CapabilityManifest,
    generate_capability_manifest,
)
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition


class CapabilityManifestTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry()

    def test_manifest_projection_from_registry(self):
        def dummy_handler(ctx, inputs):
            return {"out": "ok"}

        defn = NodeDefinition(
            type_id="test.sample_op",
            title="Sample Op",
            category="Testing",
            inputs={"src": PortDefinition(DataType.TEXT, required=True)},
            outputs={"out": PortDefinition(DataType.TEXT)},
            cache_policy=CachePolicy.PURE,
        )
        self.registry.register(defn, dummy_handler)

        manifest = generate_capability_manifest(self.registry)
        self.assertIsInstance(manifest, CapabilityManifest)
        self.assertIn("test.sample_op", manifest.capabilities)

        cap = manifest.capabilities["test.sample_op"]
        self.assertIsInstance(cap, CapabilityDefinition)
        self.assertEqual(cap.capability_id, "test.sample_op")
        self.assertEqual(cap.title, "Sample Op")
        self.assertEqual(cap.category, "Testing")
        self.assertIn("src", cap.inputs)
        self.assertTrue(cap.inputs["src"].required)
        self.assertEqual(cap.inputs["src"].data_type, "text")
        self.assertIn("out", cap.outputs)
        self.assertEqual(cap.outputs["out"].data_type, "text")
        self.assertEqual(cap.cache_policy, "pure")

    def test_manifest_serialization_to_dict_and_json(self):
        manifest = generate_capability_manifest(self.registry)
        data = manifest.to_dict()
        self.assertIn("version", data)
        self.assertIn("capabilities", data)
        json_str = manifest.to_json()
        self.assertIn('"capabilities":', json_str)


if __name__ == "__main__":
    unittest.main()

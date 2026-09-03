import importlib
import unittest

from ktools_core.builtin import register_builtin_nodes
from ktools_core.models import CachePolicy, DataType
from ktools_core.registry import NodeRegistry


class MediaExtractAudioV1RedContracts(unittest.TestCase):
    @staticmethod
    def _registry() -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        return registry

    @staticmethod
    def _product():
        api = importlib.import_module("ktools_media.api")
        node = importlib.import_module("ktools_media.node")
        return api, node

    def test_media_product_modules_exist(self) -> None:
        api, node = self._product()
        self.assertTrue(callable(api.extract_audio_from_video))
        self.assertTrue(callable(node.register_nodes))

    def test_media_extract_audio_node_contract(self) -> None:
        _, node = self._product()
        registry = self._registry()
        node.register_nodes(registry)
        definition = registry.definition("media.extract_audio")
        
        self.assertEqual(definition.inputs["video"].type, DataType.FILE)
        self.assertEqual(definition.outputs["audio"].type, DataType.AUDIO)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)


if __name__ == "__main__":
    unittest.main()

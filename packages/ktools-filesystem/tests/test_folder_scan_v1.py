from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from ktools_core.builtin import register_builtin_nodes
from ktools_core.models import CachePolicy, DataType
from ktools_core.registry import NodeRegistry


class FolderScanV1RedContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _registry() -> NodeRegistry:
        registry = NodeRegistry()
        register_builtin_nodes(registry)
        return registry

    @staticmethod
    def _product():
        scanner = importlib.import_module("ktools_filesystem.scanner")
        api = importlib.import_module("ktools_filesystem.api")
        node = importlib.import_module("ktools_filesystem.node")
        return scanner, api, node

    def test_folder_literal_contract_exists_and_is_never(self) -> None:
        definition = self._registry().definition("folder.literal")
        self.assertEqual(definition.outputs["folder"].type, DataType.FOLDER)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_filesystem_product_modules_exist(self) -> None:
        scanner, api, node = self._product()
        self.assertTrue(callable(scanner.scan_files))
        self.assertTrue(hasattr(scanner, "FolderScanError"))
        self.assertTrue(callable(api.scan_folder_files))
        self.assertTrue(callable(node.register_nodes))

    def test_folder_scan_node_contract_is_folder_to_file_set_and_json_never(self) -> None:
        _, _, node = self._product()
        registry = self._registry()
        node.register_nodes(registry)
        definition = registry.definition("folder.scan_files")
        self.assertEqual(definition.inputs["folder"].type, DataType.FOLDER)
        self.assertEqual(definition.outputs["files"].type, DataType.FILE_SET)
        self.assertEqual(definition.outputs["report"].type, DataType.JSON)
        self.assertEqual(definition.version, "1")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_scanner_accepts_valid_empty_root_as_empty_success(self) -> None:
        scanner, _, _ = self._product()
        result = scanner.scan_files(self.root)
        self.assertEqual(list(result.files), [])
        self.assertEqual(result.report["fileCount"], 0)
        self.assertEqual(result.report["errorCount"], 0)


if __name__ == "__main__":
    unittest.main()

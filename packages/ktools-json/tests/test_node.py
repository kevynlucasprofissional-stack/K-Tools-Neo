"""Node adapter and contract tests."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from ktools_core import CachePolicy, DataType, NodeRegistry

from ktools_json import JsonSplitError, register_nodes
from ktools_json import capability, node
from ktools_json.node import (
    LITERAL_TYPE_ID,
    NODE_TYPE_ID,
    PLAN_TYPE_ID,
    _json_split_handler,
    _json_split_plan_handler,
)

RECORDS = {"records": [{"id": i} for i in range(5)]}


def make_registry() -> NodeRegistry:
    registry = NodeRegistry()
    register_nodes(registry)
    return registry


class NodeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name) / "out"
        self.registry = make_registry()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_node_definition_typed_ports(self) -> None:
        definition = self.registry.definition(NODE_TYPE_ID)
        self.assertEqual(definition.type_id, "json.split")
        self.assertEqual(definition.inputs["json_data"].type, DataType.JSON)
        self.assertTrue(definition.inputs["json_data"].required)
        self.assertEqual(definition.outputs["parts"].type, DataType.JSON)
        self.assertEqual(definition.outputs["summary"].type, DataType.JSON)

        plan = self.registry.definition(PLAN_TYPE_ID)
        self.assertEqual(plan.inputs["json_data"].type, DataType.JSON)
        self.assertEqual(plan.outputs["plan"].type, DataType.JSON)

    def test_cache_policies_are_explicit_and_preserve_split_side_effects(self) -> None:
        split = self.registry.definition(NODE_TYPE_ID)
        plan = self.registry.definition(PLAN_TYPE_ID)
        literal = self.registry.definition(LITERAL_TYPE_ID)
        self.assertEqual(split.version, "1")
        self.assertIs(split.cache_policy, CachePolicy.NEVER)
        self.assertEqual(plan.version, "1")
        self.assertIs(plan.cache_policy, CachePolicy.PURE)
        self.assertEqual(literal.version, "1")
        self.assertIs(literal.cache_policy, CachePolicy.PURE)

    def test_plan_node_exposes_real_pure_split_capability_without_io(self) -> None:
        outputs = self.registry.execute(
            PLAN_TYPE_ID,
            {"json_data": RECORDS},
            {"mode": "parts", "parts": 2},
            None,  # type: ignore[arg-type]
        )
        plan = outputs["plan"]
        self.assertEqual(plan["listPath"], "$.records")
        self.assertEqual(plan["itemCount"], 5)
        self.assertEqual(plan["partCount"], 2)
        self.assertEqual([len(chunk) for chunk in plan["chunks"]], [3, 2])
        self.assertFalse(self.out.exists())

    def test_handler_produces_parts_and_summary(self) -> None:
        outputs = self.registry.execute(
            NODE_TYPE_ID,
            {"json_data": RECORDS},
            {"mode": "parts", "parts": 2, "output_dir": str(self.out), "prefix": "r"},
            None,  # type: ignore[arg-type]
        )
        self.assertEqual(len(outputs["parts"]), 2)
        self.assertEqual(outputs["summary"]["partCount"], 2)
        files = list(self.out.iterdir())
        self.assertEqual(len(files), 2)

    def test_handler_requires_output_dir(self) -> None:
        with self.assertRaises(JsonSplitError):
            self.registry.execute(
                NODE_TYPE_ID,
                {"json_data": RECORDS},
                {"mode": "parts", "parts": 2},
                None,  # type: ignore[arg-type]
            )

    def test_handler_validates_mode(self) -> None:
        from ktools_json import InvalidModeError

        with self.assertRaises(InvalidModeError):
            self.registry.execute(
                NODE_TYPE_ID,
                {"json_data": RECORDS},
                {"mode": "wrong", "output_dir": str(self.out)},
                None,  # type: ignore[arg-type]
            )

    def test_handler_validates_parts_type_from_config(self) -> None:
        from ktools_json import InvalidPartsError

        with self.assertRaises(InvalidPartsError):
            self.registry.execute(
                NODE_TYPE_ID,
                {"json_data": RECORDS},
                {"mode": "parts", "parts": "3", "output_dir": str(self.out)},
                None,  # type: ignore[arg-type]
            )

    def test_literal_node(self) -> None:
        outputs = self.registry.execute(
            "json.literal",
            {},
            {"value": {"a": 1}},
            None,  # type: ignore[arg-type]
        )
        self.assertEqual(outputs["json"], {"a": 1})


class NoDuplicatedLogicTests(unittest.TestCase):
    def test_adapter_contains_no_split_algorithms(self) -> None:
        """Structural guard: adapters must not re-implement the split algorithms."""
        for handler in (_json_split_handler, _json_split_plan_handler):
            src = inspect.getsource(handler)
            for symbol in (
                "split_evenly",
                "chunk_by_target_size",
                "find_largest_list",
                "replace_at_path",
            ):
                self.assertNotIn(symbol, src)

    def test_node_build_options_uses_make_options(self) -> None:
        """Config-to-options conversion is shared with the direct API."""
        self.assertIn("make_options", inspect.getsource(node.build_options))

    def test_file_handler_delegates_to_shared_split_and_write(self) -> None:
        src = inspect.getsource(_json_split_handler)
        self.assertIn("split_and_write", src)

    def test_plan_handler_delegates_to_shared_pure_capability(self) -> None:
        src = inspect.getsource(node._plan_payload)
        self.assertIn("split_json_document", src)


if __name__ == "__main__":
    unittest.main()

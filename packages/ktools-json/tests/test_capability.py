"""Capability-level tests: the pure split semantics owner."""

from __future__ import annotations

import unittest

from ktools_json.capability import (
    EmptyMainListError,
    InvalidModeError,
    InvalidPartsError,
    InvalidTargetSizeError,
    NoMainListError,
    SplitOptions,
    chunk_by_target_size,
    estimate_bytes,
    find_largest_list,
    json_path_label,
    make_options,
    replace_at_path,
    split_evenly,
    split_json_document,
)


class FindLargestListTests(unittest.TestCase):
    def test_root_list_is_the_main_list(self) -> None:
        data = [1, 2, 3]
        path, items = find_largest_list(data)
        self.assertEqual(path, ())
        self.assertEqual(items, [1, 2, 3])

    def test_largest_semantic_list_wins(self) -> None:
        data = {"a": {"records": [1, 2, 3, 4]}, "b": {"records": [1, 2]}}
        path, items = find_largest_list(data)
        self.assertEqual(path, ("a", "records"))
        self.assertEqual(len(items), 4)

    def test_empty_object_with_no_list(self) -> None:
        path, items = find_largest_list({"a": {"b": "x"}})
        self.assertEqual(path, ())
        self.assertEqual(items, [])

    def test_list_nested_inside_item_is_avoided(self) -> None:
        data = {
            "items": [
                {"tags": ["x", "y"], "extra": 1},
                {"tags": ["z"], "extra": 2},
            ]
        }
        path, items = find_largest_list(data)
        # "items" is semantic (5-element reachable through the object key "items").
        self.assertEqual(path, ("items",))
        self.assertEqual(len(items), 2)


class JsonPathLabelTests(unittest.TestCase):
    def test_root_label(self) -> None:
        self.assertEqual(json_path_label(()), "$")

    def test_simple_key_label(self) -> None:
        self.assertEqual(json_path_label(("records",)), "$.records")

    def test_key_with_spaces_uses_bracket_quote(self) -> None:
        self.assertEqual(json_path_label(("my key",)), "$['my key']")


class ReplaceAtPathTests(unittest.TestCase):
    def test_replace_does_not_mutate_input(self) -> None:
        original = {"records": [1, 2, 3], "keep": True}
        replaced = replace_at_path(original, ("records",), [1])
        self.assertEqual(original["records"], [1, 2, 3])
        self.assertEqual(replaced["records"], [1])
        self.assertTrue(replaced["keep"])

    def test_replace_root(self) -> None:
        self.assertEqual(replace_at_path([1, 2, 3], (), [9]), [9])


class MakeOptionsTests(unittest.TestCase):
    def test_defaults(self) -> None:
        options = make_options()
        self.assertEqual(options.mode, "parts")
        self.assertEqual(options.parts, 2)

    def test_invalid_mode(self) -> None:
        with self.assertRaises(InvalidModeError):
            make_options(mode="chunks")

    def test_invalid_parts_zero(self) -> None:
        with self.assertRaises(InvalidPartsError):
            make_options(parts=0)

    def test_invalid_parts_float(self) -> None:
        with self.assertRaises(InvalidPartsError):
            make_options(parts=2.0)

    def test_invalid_parts_string(self) -> None:
        with self.assertRaises(InvalidPartsError):
            make_options(parts="2")

    def test_invalid_target_zero(self) -> None:
        with self.assertRaises(InvalidTargetSizeError):
            make_options(mode="size", target_bytes=0)

    def test_invalid_target_string(self) -> None:
        with self.assertRaises(InvalidTargetSizeError):
            make_options(mode="size", target_bytes="100")


class SplitEvenlyTests(unittest.TestCase):
    def test_even_split(self) -> None:
        chunks = split_evenly([1, 2, 3, 4, 5], 2)
        self.assertEqual(chunks, [[1, 2, 3], [4, 5]])

    def test_more_parts_than_items_clamps(self) -> None:
        chunks = split_evenly([1, 2], 5)
        self.assertEqual(chunks, [[1], [2]])

    def test_single_part(self) -> None:
        chunks = split_evenly([1, 2, 3], 1)
        self.assertEqual(chunks, [[1, 2, 3]])


class SizeChunkTests(unittest.TestCase):
    def test_chunks_stay_within_target(self) -> None:
        data = {"records": [{"v": "x" * 50} for _ in range(25)]}
        target = 1000
        chunks = chunk_by_target_size(data, ("records",), data["records"], target)
        self.assertGreaterEqual(len(chunks), 2)
        overhead = estimate_bytes(replace_at_path(data, ("records",), []))
        for chunk in chunks:
            size = estimate_bytes(replace_at_path(data, ("records",), chunk))
            self.assertLessEqual(size, target + 100)  # small estimation slack

    def test_single_chunk_when_small(self) -> None:
        data = {"records": [1, 2]}
        chunks = chunk_by_target_size(data, ("records",), data["records"], 10_000)
        self.assertEqual(len(chunks), 1)


class SplitJsonDocumentTests(unittest.TestCase):
    def test_parts_plan(self) -> None:
        data = {"records": [{"id": i} for i in range(5)]}
        plan = split_json_document(data, make_options(parts=2))
        self.assertEqual(plan.root_type, "dict")
        self.assertEqual(plan.list_path, ("records",))
        self.assertEqual(plan.list_path_label, "$.records")
        self.assertEqual(plan.item_count, 5)
        self.assertEqual(plan.part_count, 2)
        self.assertEqual([len(c) for c in plan.chunks], [3, 2])
        self.assertEqual(len(plan.estimated_sizes), 2)

    def test_no_main_list_error(self) -> None:
        with self.assertRaises(NoMainListError):
            split_json_document({"a": {"b": 1}}, make_options(parts=2))

    def test_empty_root_list_error(self) -> None:
        with self.assertRaises(EmptyMainListError):
            split_json_document([], make_options(parts=2))

    def test_deterministic_plan(self) -> None:
        data = {"records": [{"id": i} for i in range(5)]}
        plan_a = split_json_document(data, make_options(parts=2))
        plan_b = split_json_document(data, make_options(parts=2))
        self.assertEqual(plan_a.chunks, plan_b.chunks)
        self.assertEqual(plan_a.estimated_sizes, plan_b.estimated_sizes)

    def test_unchanged_by_order_of_equal_items(self) -> None:
        data = {"records": [{"id": 1, "t": "a"}, {"id": 2, "t": "b"}, {"id": 3, "t": "c"}]}
        plan = split_json_document(data, make_options(parts=2))
        self.assertEqual(list(plan.chunks), [data["records"][:2], data["records"][2:]])


class SplitOptionsConstructionTests(unittest.TestCase):
    def test_invalid_mode_raised_at_construction(self) -> None:
        with self.assertRaises(InvalidModeError):
            SplitOptions(mode="bad")

    def test_invalid_parts_raised_at_construction(self) -> None:
        with self.assertRaises(InvalidPartsError):
            SplitOptions(mode="parts", parts=0)


if __name__ == "__main__":
    unittest.main()
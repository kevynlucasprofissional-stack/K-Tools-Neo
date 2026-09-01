"""Direct API tests: file boundary, failure semantics, determinism."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ktools_json.api import (
    InvalidJsonDocumentError,
    JsonSourceError,
    split_json,
)
from ktools_json.writer import OutputCollisionError
from ktools_json import InvalidPartsError, NoMainListError


class SplitJsonApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _source(self, payload, name: str = "source.json") -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_parts_happy_path(self) -> None:
        source = self._source(
            {"dataset": "oc001", "records": [{"id": i} for i in range(5)]}
        )
        out = self.root / "out"
        result = split_json(source, out, mode="parts", parts=2, prefix="records")

        self.assertEqual(result.summary["partCount"], 2)
        self.assertEqual(result.summary["itemCount"], 5)
        written = sorted(path.name for path in out.iterdir())
        self.assertEqual(written, ["records_parte_01_de_02.json", "records_parte_02_de_02.json"])

        first = json.loads((out / "records_parte_01_de_02.json").read_text(encoding="utf-8"))
        self.assertEqual(first["dataset"], "oc001")  # surrounding structure preserved
        self.assertEqual(first["records"], [{"id": 0}, {"id": 1}, {"id": 2}])
        for part in result.parts:
            record = part.to_dict()
            self.assertEqual(record["kind"], "file")
            self.assertEqual(record["type"], "json")
            self.assertTrue(record["uri"].startswith("file://"))
            self.assertGreater(record["sizeBytes"], 0)
            self.assertGreater(record["itemCount"], 0)

    def test_size_mode(self) -> None:
        source = self._source({"records": [{"v": "x" * 100} for _ in range(40)]})
        out = self.root / "out"
        result = split_json(source, out, mode="size", target_bytes=1000, prefix="chunk")

        self.assertGreater(result.summary["partCount"], 1)
        files = list(out.iterdir())
        self.assertEqual(len(files), result.summary["partCount"])
        for part in result.parts:
            self.assertLessEqual(part.size_bytes, 1300)  # estimation slack on disk bytes

    def test_utf8_accented_content_round_trips(self) -> None:
        source = self._source({"records": [{"nome": "João"}, {"nome": "Coração"}]})
        out = self.root / "out"
        result = split_json(source, out, mode="parts", parts=2)
        first = json.loads((out / result.parts[0].name).read_text(encoding="utf-8"))
        self.assertEqual(first["records"][0]["nome"], "João")

    def test_missing_source(self) -> None:
        with self.assertRaises(JsonSourceError):
            split_json(self.root / "nope.json", self.root / "out", parts=2)

    def test_invalid_json_content(self) -> None:
        path = self.root / "bad.json"
        path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(InvalidJsonDocumentError):
            split_json(path, self.root / "out", parts=2)

    def test_invalid_parts_config(self) -> None:
        source = self._source({"records": [1, 2, 3]})
        with self.assertRaises(InvalidPartsError):
            split_json(source, self.root / "out", parts=0)

    def test_no_main_list(self) -> None:
        source = self._source({"a": {"b": 1}})
        with self.assertRaises(NoMainListError):
            split_json(source, self.root / "out", parts=2)

    def test_default_refuses_overwrite(self) -> None:
        source = self._source({"records": [1, 2, 3, 4]})
        out = self.root / "out"
        split_json(source, out, mode="parts", parts=2, prefix="records")
        with self.assertRaises(OutputCollisionError):
            split_json(source, out, mode="parts", parts=2, prefix="records")

    def test_deterministic_output_across_runs(self) -> None:
        source = self._source({"records": [{"id": i} for i in range(6)]})
        out_a = self.root / "a"
        out_b = self.root / "b"
        result_a = split_json(source, out_a, mode="parts", parts=3, prefix="r")
        result_b = split_json(source, out_b, mode="parts", parts=3, prefix="r")

        names_a = [p.name for p in result_a.parts]
        names_b = [p.name for p in result_b.parts]
        self.assertEqual(names_a, names_b)
        for part_a, part_b in zip(result_a.parts, result_b.parts):
            self.assertEqual(part_a.size_bytes, part_b.size_bytes)
            self.assertEqual(part_a.item_count, part_b.item_count)
            content_a = (out_a / part_a.name).read_bytes()
            content_b = (out_b / part_b.name).read_bytes()
            self.assertEqual(content_a, content_b)
        self.assertEqual(result_a.summary, result_b.summary)


if __name__ == "__main__":
    unittest.main()
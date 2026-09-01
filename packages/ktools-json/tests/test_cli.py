"""CLI smoke tests: real headless workflow execution boundary."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ktools_core import RunStatus, SQLiteRunJournal
from ktools_json import cli

RECORDS = {"dataset": "oc001", "records": [{"id": i} for i in range(5)]}


def write_workflow(path: Path, output_dir: str) -> Path:
    workflow = {
        "id": "cli-oc001",
        "nodes": [
            {"id": "source", "type": "json.literal", "config": {"value": RECORDS}},
            {
                "id": "splitter",
                "type": "json.split",
                "config": {"mode": "parts", "parts": 2, "output_dir": output_dir, "prefix": "r"},
            },
        ],
        "edges": [
            {
                "sourceNode": "source",
                "sourcePort": "json",
                "targetNode": "splitter",
                "targetPort": "json_data",
            }
        ],
    }
    path.write_text(json.dumps(workflow, ensure_ascii=False), encoding="utf-8")
    return path


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.out = self.root / "out"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_cli_executes_split_workflow(self) -> None:
        workflow = write_workflow(self.root / "wf.json", str(self.out))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main([str(workflow), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["workflowId"], "cli-oc001")
        self.assertTrue(payload["runId"].startswith("run_"))
        splitter = payload["nodeOutputs"]["splitter"]
        self.assertEqual(splitter["summary"]["partCount"], 2)
        self.assertEqual(len(splitter["parts"]), 2)
        self.assertEqual(len(list(self.out.iterdir())), 2)

    def test_cli_can_persist_real_json_workflow_journal(self) -> None:
        workflow = write_workflow(self.root / "durable.json", str(self.out))
        journal_path = self.root / "runs.sqlite3"
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main(
                [
                    str(workflow),
                    "--json",
                    "--journal",
                    str(journal_path),
                ]
            )

        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["journal"], str(journal_path))
        with SQLiteRunJournal(journal_path) as journal:
            detail = journal.get_run_detail(payload["runId"])
            self.assertIsNotNone(detail)
            assert detail is not None
            self.assertEqual(detail.run.status, RunStatus.SUCCEEDED)
            splitter = next(node for node in detail.nodes if node.node_id == "splitter")
            self.assertEqual(splitter.outputs["summary"]["partCount"], 2)

    def test_cli_validation_failure_exit_code(self) -> None:
        workflow = self.root / "bad.json"
        workflow.write_text(
            json.dumps(
                {
                    "id": "bad",
                    "nodes": [{"id": "x", "type": "does.not.exist"}],
                    "edges": [],
                }
            ),
            encoding="utf-8",
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main([str(workflow)])
        self.assertEqual(code, 2)
        self.assertIn("VALIDATION_ERROR", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
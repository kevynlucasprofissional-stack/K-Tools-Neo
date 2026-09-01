"""CLI smoke tests: real headless workflow execution boundary."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from ktools_core import NodeRunStatus, RunStatus, SQLiteRunJournal
from ktools_json import cli

RECORDS = {"dataset": "oc001", "records": [{"id": i} for i in range(5)]}


def write_workflow(
    path: Path,
    output_dir: str,
    *,
    mode: str = "parts",
    overwrite: bool = False,
) -> Path:
    workflow = {
        "id": "cli-oc001",
        "nodes": [
            {"id": "source", "type": "json.literal", "config": {"value": RECORDS}},
            {
                "id": "splitter",
                "type": "json.split",
                "config": {
                    "mode": mode,
                    "parts": 2,
                    "output_dir": output_dir,
                    "prefix": "r",
                    "overwrite": overwrite,
                },
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
        self.diag = self.root / "diagnostics"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_cli_executes_split_workflow_and_generates_diagnostics(self) -> None:
        workflow = write_workflow(self.root / "wf.json", str(self.out))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main([str(workflow), "--json", "--diagnostics-dir", str(self.diag)])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["workflowId"], "cli-oc001")
        self.assertTrue(payload["runId"].startswith("run_"))
        splitter = payload["nodeOutputs"]["splitter"]
        self.assertEqual(splitter["summary"]["partCount"], 2)
        self.assertEqual(len(splitter["parts"]), 2)
        self.assertEqual(len(list(self.out.iterdir())), 2)

        bundle = Path(payload["diagnosticBundle"])
        self.assertTrue(bundle.exists())
        report = json.loads((bundle.parent / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["session"]["status"], "SUCCEEDED")
        self.assertEqual(report["session"]["runId"], payload["runId"])
        node_events = [event for event in report["events"] if event.get("nodeId") == "splitter"]
        self.assertTrue(node_events)
        with zipfile.ZipFile(bundle) as archive:
            self.assertIn("report.md", archive.namelist())
            self.assertIn("diagnostics.jsonl", archive.namelist())

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
                    "--diagnostics-dir",
                    str(self.diag),
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
        report = json.loads(
            (Path(payload["diagnosticBundle"]).parent / "report.json").read_text(encoding="utf-8")
        )
        self.assertTrue(report["journalEvents"])

    def test_real_node_pack_cache_reuses_literal_but_splitter_executes_again(self) -> None:
        workflow = write_workflow(
            self.root / "cached.json",
            str(self.out),
            overwrite=True,
        )
        journal_path = self.root / "cache-runs.sqlite3"
        cache_path = self.root / "node-cache.sqlite3"
        payloads: list[dict] = []

        for _ in range(2):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cli.main(
                    [
                        str(workflow),
                        "--json",
                        "--journal",
                        str(journal_path),
                        "--cache",
                        str(cache_path),
                        "--diagnostics-dir",
                        str(self.diag),
                    ]
                )
            self.assertEqual(code, 0)
            payloads.append(json.loads(buffer.getvalue()))

        self.assertEqual(payloads[1]["cache"], str(cache_path))
        with SQLiteRunJournal(journal_path) as journal:
            detail = journal.get_run_detail(payloads[1]["runId"])
            self.assertIsNotNone(detail)
            assert detail is not None
            statuses = {node.node_id: node.status for node in detail.nodes}
            self.assertIs(statuses["source"], NodeRunStatus.CACHED)
            self.assertIs(statuses["splitter"], NodeRunStatus.SUCCEEDED)

        # The second splitter execution really republishes the same deterministic files.
        self.assertEqual(len(list(self.out.glob("*.json"))), 2)
        self.assertEqual(payloads[0]["nodeOutputs"]["splitter"], payloads[1]["nodeOutputs"]["splitter"])

        report_path = Path(payloads[1]["diagnosticBundle"]).parent / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        decisions = [
            event
            for event in report["decisions"]
            if event.get("category") == "workflow.cache"
        ]
        source_reasons = {
            event["context"].get("reason")
            for event in decisions
            if event.get("nodeId") == "source"
        }
        splitter_reasons = {
            event["context"].get("reason")
            for event in decisions
            if event.get("nodeId") == "splitter"
        }
        self.assertIn("validated-cache-hit", source_reasons)
        self.assertIn("node-policy-never", splitter_reasons)

        report_md = (Path(payloads[1]["diagnosticBundle"]).parent / "report.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Cached node output reused", report_md)
        self.assertIn("Cache bypassed", report_md)

    def test_cli_validation_failure_exit_code_and_bundle(self) -> None:
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
            code = cli.main([str(workflow), "--diagnostics-dir", str(self.diag)])
        self.assertEqual(code, 2)
        output = buffer.getvalue()
        self.assertIn("VALIDATION_ERROR", output)
        diagnostic_line = next(line for line in output.splitlines() if line.startswith("DIAGNOSTICS: "))
        bundle = Path(diagnostic_line.split(": ", 1)[1])
        self.assertTrue(bundle.exists())
        report = json.loads((bundle.parent / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["session"]["status"], "VALIDATION_ERROR")
        self.assertTrue(report["errors"])

    def test_cli_execution_failure_bundle_identifies_splitter(self) -> None:
        workflow = write_workflow(self.root / "failed.json", str(self.out), mode="invalid-mode")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.main([str(workflow), "--diagnostics-dir", str(self.diag)])
        self.assertEqual(code, 3)
        output = buffer.getvalue()
        bundle = Path(
            next(line for line in output.splitlines() if line.startswith("DIAGNOSTICS: ")).split(": ", 1)[1]
        )
        report = json.loads((bundle.parent / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["session"]["status"], "FAILED")
        self.assertEqual(report["session"]["workflowId"], "cli-oc001")
        self.assertTrue(any(event.get("nodeId") == "splitter" for event in report["errors"]))


if __name__ == "__main__":
    unittest.main()

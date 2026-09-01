from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ktools_core import NodeRunStatus, RunStatus, SQLiteRunJournal
from ktools_core.cli import main


class WorkflowCliTests(unittest.TestCase):
    def test_cli_can_persist_run_and_generate_diagnostic_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_path = root / "workflow.json"
            journal_path = root / "runs.sqlite3"
            diagnostics_dir = root / "diagnostics"
            workflow_path.write_text(
                json.dumps(
                    {
                        "id": "cli-journal",
                        "nodes": [
                            {
                                "id": "hello",
                                "type": "text.literal",
                                "config": {"value": "K-Tools"},
                            }
                        ],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        str(workflow_path),
                        "--json",
                        "--journal",
                        str(journal_path),
                        "--diagnostics-dir",
                        str(diagnostics_dir),
                    ]
                )

            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["workflowId"], "cli-journal")
            self.assertEqual(payload["journal"], str(journal_path))
            self.assertTrue(payload["runId"].startswith("run_"))

            bundle = Path(payload["diagnosticBundle"])
            self.assertTrue(bundle.exists())
            report = json.loads((bundle.parent / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["session"]["runId"], payload["runId"])
            self.assertEqual(report["session"]["status"], "SUCCEEDED")
            self.assertTrue(report["journalEvents"])

            with SQLiteRunJournal(journal_path) as journal:
                run = journal.get_run(payload["runId"])
                self.assertIsNotNone(run)
                assert run is not None
                self.assertEqual(run.status, RunStatus.SUCCEEDED)
                self.assertEqual(run.workflow_id, "cli-journal")

    def test_cli_cache_survives_separate_invocations_and_projects_cached_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_path = root / "workflow.json"
            cache_path = root / "cache.sqlite3"
            journal_path = root / "runs.sqlite3"
            workflow_path.write_text(
                json.dumps(
                    {
                        "id": "cli-cache",
                        "nodes": [
                            {
                                "id": "hello",
                                "type": "text.literal",
                                "config": {"value": "cached"},
                            }
                        ],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )

            payloads = []
            for _ in range(2):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    code = main(
                        [
                            str(workflow_path),
                            "--json",
                            "--journal",
                            str(journal_path),
                            "--cache",
                            str(cache_path),
                            "--no-diagnostics",
                        ]
                    )
                self.assertEqual(code, 0)
                payloads.append(json.loads(stdout.getvalue()))

            self.assertEqual(payloads[0]["cache"], str(cache_path))
            self.assertEqual(payloads[1]["cache"], str(cache_path))
            self.assertNotEqual(payloads[0]["runId"], payloads[1]["runId"])
            self.assertEqual(payloads[1]["nodeOutputs"]["hello"]["text"], "cached")

            with SQLiteRunJournal(journal_path) as journal:
                detail = journal.get_run_detail(payloads[1]["runId"])
                self.assertIsNotNone(detail)
                assert detail is not None
                self.assertEqual(len(detail.nodes), 1)
                self.assertIs(detail.nodes[0].status, NodeRunStatus.CACHED)

    def test_no_diagnostics_remains_available_for_minimal_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_path = root / "workflow.json"
            workflow_path.write_text(
                json.dumps(
                    {
                        "id": "minimal",
                        "nodes": [{"id": "hello", "type": "text.literal", "config": {"value": "x"}}],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main([str(workflow_path), "--json", "--no-diagnostics"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertNotIn("diagnosticBundle", payload)


if __name__ == "__main__":
    unittest.main()

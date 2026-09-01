from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ktools_core import RunStatus, SQLiteRunJournal
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

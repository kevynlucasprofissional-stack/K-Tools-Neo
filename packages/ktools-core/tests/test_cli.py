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
    def test_cli_can_persist_run_to_sqlite_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_path = root / "workflow.json"
            journal_path = root / "runs.sqlite3"
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
                    ]
                )

            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["workflowId"], "cli-journal")
            self.assertEqual(payload["journal"], str(journal_path))
            self.assertTrue(payload["runId"].startswith("run_"))

            with SQLiteRunJournal(journal_path) as journal:
                run = journal.get_run(payload["runId"])
                self.assertIsNotNone(run)
                assert run is not None
                self.assertEqual(run.status, RunStatus.SUCCEEDED)
                self.assertEqual(run.workflow_id, "cli-journal")


if __name__ == "__main__":
    unittest.main()

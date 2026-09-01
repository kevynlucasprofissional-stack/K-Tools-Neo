from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from ktools_core.cli import main


class CliInterruptTests(unittest.TestCase):
    def test_keyboard_interrupt_generates_interrupted_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow = root / "workflow.json"
            diagnostics_dir = root / "diagnostics"
            workflow.write_text(
                json.dumps(
                    {
                        "id": "interrupt-test",
                        "nodes": [{"id": "hello", "type": "text.literal", "config": {"value": "x"}}],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )
            fake_engine = mock.Mock()
            fake_engine.execute.side_effect = KeyboardInterrupt()
            stdout = StringIO()
            with mock.patch("ktools_core.cli.build_engine", return_value=fake_engine), redirect_stdout(stdout):
                code = main([str(workflow), "--diagnostics-dir", str(diagnostics_dir)])

            self.assertEqual(code, 130)
            lines = stdout.getvalue().splitlines()
            self.assertTrue(any(line.startswith("INTERRUPTED:") for line in lines))
            bundle_line = next(line for line in lines if line.startswith("DIAGNOSTICS: "))
            bundle = Path(bundle_line.split(": ", 1)[1])
            self.assertTrue(bundle.exists())
            report = json.loads((bundle.parent / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["session"]["status"], "INTERRUPTED")
            session = json.loads((bundle.parent / "session.json").read_text(encoding="utf-8"))
            self.assertEqual(session["status"], "INTERRUPTED")


if __name__ == "__main__":
    unittest.main()

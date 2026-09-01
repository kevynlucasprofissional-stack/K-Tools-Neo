from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from ktools_core import DiagnosticKind, DiagnosticsSession


class DiagnosticFailureBoundaryTests(unittest.TestCase):
    def test_subprocess_timeout_is_recorded_and_returns_timed_out_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session = DiagnosticsSession(Path(temp_dir), session_id="diag-timeout", component="tests")
            result = session.run_subprocess(
                [sys.executable, "-c", "import time; print('before-sleep'); time.sleep(2)"],
                timeout=0.05,
            )
            self.assertTrue(result.timed_out)
            self.assertIsNone(result.return_code)
            self.assertIsNotNone(result.stdout_path)
            self.assertTrue(any(event.kind is DiagnosticKind.EXCEPTION for event in session.events))
            bundle = session.finalize(status="FAILED")
            self.assertTrue(bundle.exists())

    def test_subprocess_launch_failure_is_recorded_without_crashing_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session = DiagnosticsSession(Path(temp_dir), session_id="diag-launch", component="tests")
            result = session.run_subprocess(["ktools-command-that-does-not-exist-9f41"])
            self.assertIsNone(result.return_code)
            self.assertIsNotNone(result.launch_error)
            self.assertTrue(any(event.kind is DiagnosticKind.EXCEPTION for event in session.events))
            bundle = session.finalize(status="FAILED")
            self.assertTrue(bundle.exists())


if __name__ == "__main__":
    unittest.main()

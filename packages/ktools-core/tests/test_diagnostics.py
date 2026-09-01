from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from ktools_core import (
    DiagnosticKind,
    DiagnosticLogHandler,
    DiagnosticSeverity,
    DiagnosticsSession,
    recover_abandoned_sessions,
    redact_command,
    redact_value,
)


class RedactionTests(unittest.TestCase):
    def test_recursive_secret_keys_and_inline_values_are_redacted(self) -> None:
        value = redact_value(
            {
                "api_key": "SUPER-SECRET",
                "nested": {"password": "hunter2", "safe": "ok"},
                "message": "Authorization: Bearer abc123",
                "url": "https://example.test/?token=abc123&x=1",
            }
        )
        serialized = json.dumps(value, sort_keys=True)
        self.assertNotIn("SUPER-SECRET", serialized)
        self.assertNotIn("hunter2", serialized)
        self.assertNotIn("abc123", serialized)
        self.assertEqual(value["nested"]["safe"], "ok")

    def test_command_argument_secret_is_redacted(self) -> None:
        command = redact_command(["tool", "--token", "abc123", "--api-key=xyz", "safe"])
        self.assertEqual(command[2], "<redacted>")
        self.assertEqual(command[3], "--api-key=<redacted>")
        self.assertNotIn("abc123", json.dumps(command))
        self.assertNotIn("xyz", json.dumps(command))

    def test_unknown_object_repr_is_not_persisted(self) -> None:
        class Dangerous:
            def __repr__(self) -> str:
                return "password=DO-NOT-LEAK"

        serialized = json.dumps(redact_value(Dangerous()), sort_keys=True)
        self.assertNotIn("DO-NOT-LEAK", serialized)
        self.assertIn("__nonSerializable__", serialized)


class DiagnosticsSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_session_generates_shareable_report_and_bundle(self) -> None:
        session = DiagnosticsSession(self.root, session_id="diag-test", component="tests")
        session.decision("Selected fallback", reason="primary unavailable", context={"token": "SECRET"})
        session.metric("items", 7, unit="count")
        session.batch("Batch completed", batch_id="batch-1", context={"processed": 7})
        session.anomaly("Expected 8 items but observed 7", context={"expected": 8, "actual": 7})
        try:
            raise RuntimeError("password=SHOULD-NOT-LEAK")
        except RuntimeError as exc:
            session.capture_exception(exc, "Synthetic failure for diagnostics test")

        bundle = session.finalize(status="FAILED", run_id="run_test", workflow_id="wf_test")
        self.assertTrue(bundle.exists())
        report = json.loads((session.root / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["session"]["status"], "FAILED")
        self.assertEqual(report["session"]["runId"], "run_test")
        self.assertGreaterEqual(report["summary"]["noteworthyCount"], 2)
        self.assertTrue(report["decisions"])
        self.assertTrue(report["batches"])
        self.assertTrue(report["metrics"])
        self.assertTrue(report["anomalies"])
        self.assertTrue(report["errors"])

        share_text = (
            (session.root / "report.md").read_text(encoding="utf-8")
            + (session.root / "report.json").read_text(encoding="utf-8")
            + (session.root / "diagnostics.jsonl").read_text(encoding="utf-8")
        )
        self.assertNotIn("SECRET", share_text)
        self.assertNotIn("SHOULD-NOT-LEAK", share_text)

        with zipfile.ZipFile(bundle) as archive:
            names = set(archive.namelist())
            self.assertIn("report.md", names)
            self.assertIn("report.json", names)
            self.assertIn("diagnostics.jsonl", names)
            for name in names:
                if name.endswith((".json", ".jsonl", ".md", ".log")):
                    text = archive.read(name).decode("utf-8")
                    self.assertNotIn("SHOULD-NOT-LEAK", text)

    def test_subprocess_captures_stdout_stderr_and_exit_code(self) -> None:
        session = DiagnosticsSession(self.root, session_id="diag-process", component="tests")
        result = session.run_subprocess(
            [
                sys.executable,
                "-c",
                "import sys; print('hello-out'); print('hello-err', file=sys.stderr); sys.exit(7)",
            ]
        )
        self.assertEqual(result.return_code, 7)
        self.assertIsNotNone(result.stdout_path)
        self.assertIsNotNone(result.stderr_path)
        self.assertIn("hello-out", Path(result.stdout_path).read_text(encoding="utf-8"))
        self.assertIn("hello-err", Path(result.stderr_path).read_text(encoding="utf-8"))
        subprocess_events = [event for event in session.events if event.kind is DiagnosticKind.SUBPROCESS]
        self.assertEqual(len(subprocess_events), 2)
        self.assertEqual(subprocess_events[-1].severity, DiagnosticSeverity.ERROR)
        session.finalize(status="FAILED")

    def test_subprocess_raw_logs_redact_inline_secret_patterns(self) -> None:
        session = DiagnosticsSession(self.root, session_id="diag-secret-process", component="tests")
        result = session.run_subprocess([sys.executable, "-c", "print('token=VERYSECRET')"])
        raw = Path(result.stdout_path).read_text(encoding="utf-8")
        self.assertNotIn("VERYSECRET", raw)
        self.assertIn("<redacted>", raw)
        session.finalize(status="SUCCEEDED")

    def test_standard_logging_handler_captures_message_and_exception(self) -> None:
        session = DiagnosticsSession(self.root, session_id="diag-logging", component="tests")
        logger = logging.getLogger("ktools.tests.diagnostics")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        handler = DiagnosticLogHandler(session)
        logger.addHandler(handler)
        try:
            logger.warning("low confidence score=%s", 0.31)
            try:
                raise ValueError("token=LOGGERSECRET")
            except ValueError:
                logger.exception("model stage failed")
        finally:
            logger.removeHandler(handler)
            handler.close()
        events = [event for event in session.events if event.category == "python.logging"]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].severity, DiagnosticSeverity.WARNING)
        self.assertEqual(events[1].kind, DiagnosticKind.EXCEPTION)
        session.finalize(status="FAILED")
        text = (session.root / "diagnostics.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("LOGGERSECRET", text)

    def test_abandoned_session_is_recovered_to_shareable_bundle(self) -> None:
        session = DiagnosticsSession(self.root, session_id="diag-abandoned", component="tests")
        session.log("Started batch", batch_id="batch-1")
        session.anomaly("Worker stopped responding")
        # Simulate abrupt death by intentionally not calling finalize().
        recovered = recover_abandoned_sessions(self.root)
        self.assertEqual(len(recovered), 1)
        bundle = recovered[0]
        self.assertTrue(bundle.exists())
        report = json.loads((session.root / "report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["recoveredAbandonedSession"])
        self.assertEqual(report["session"]["status"], "ABANDONED_OR_INTERRUPTED")
        self.assertEqual(recover_abandoned_sessions(self.root), ())

    @unittest.skipUnless(shutil.which("pwsh") or shutil.which("powershell"), "PowerShell unavailable")
    def test_powershell_output_can_be_captured_when_available(self) -> None:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        session = DiagnosticsSession(self.root, session_id="diag-powershell", component="tests")
        result = session.run_subprocess(
            [executable, "-NoProfile", "-Command", "Write-Output 'ps-out'; [Console]::Error.WriteLine('ps-err')"]
        )
        self.assertEqual(result.return_code, 0)
        self.assertIn("ps-out", Path(result.stdout_path).read_text(encoding="utf-8"))
        self.assertIn("ps-err", Path(result.stderr_path).read_text(encoding="utf-8"))
        session.finalize(status="SUCCEEDED")


if __name__ == "__main__":
    unittest.main()

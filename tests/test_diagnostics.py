
from pathlib import Path
from yt_dlp_tui.diagnostics.context import RunContext
from yt_dlp_tui.diagnostics.logger import DiagnosticLogger

def test_event_run_id_and_redaction(tmp_path):
    log=tmp_path/"events.jsonl"
    logger=DiagnosticLogger(RunContext(), str(log))
    evt=logger.emit("test","START",data={"cookie":"abc","value":1})
    assert evt.run_id
    text=log.read_text(encoding="utf8")
    assert "abc" not in text
    assert "<redacted>" in text

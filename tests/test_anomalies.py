from yt_dlp_tui.diagnostics.anomalies import detect_anomalies


def test_empty_playlist_is_anomaly():
    result = detect_anomalies([{"event":"PLAYLIST_DETECTED", "data":{"entries":0}}])
    assert result[0]["type"] == "ANOMALY_PLAYLIST_EMPTY"


def test_missing_completed_file_is_detected(tmp_path):
    result = detect_anomalies([], {"items":[{"status":"completed", "video_id":"a", "final_file":str(tmp_path/'x.mp4')}]})
    assert result[0]["type"] == "CONTROL_FILE_MISMATCH"


def test_audit_cannot_pass_with_failed_files():
    result = detect_anomalies([], audit={"status":"passed", "failed":1})
    assert result[0]["type"] == "AUDIT_RESULT_INCONSISTENT"

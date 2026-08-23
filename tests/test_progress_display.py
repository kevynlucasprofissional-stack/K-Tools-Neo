import io
import sys
import types

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import downloader


def test_progress_prefers_numeric_byte_counters_over_colored_percent_text():
    payload = {
        "downloaded_bytes": 565,
        "total_bytes": 1000,
        "_percent_str": "\x1b[0;32m  0.0%\x1b[0m",
    }
    assert downloader._progress_percent(payload) == 56.5


def test_progress_parses_ansi_colored_percent_when_bytes_are_unavailable():
    payload = {"_percent_str": "\x1b[0;32m 56.5%\x1b[0m"}
    assert downloader._progress_percent(payload) == 56.5


def test_progress_uses_fragment_counters_as_fallback():
    payload = {"fragment_index": 3, "fragment_count": 4}
    assert downloader._progress_percent(payload) == 75.0


def test_item_tracker_persists_real_percentage(tmp_path, monkeypatch):
    saved = []
    monkeypatch.setattr(downloader, "save_control", lambda task_dir, state: saved.append(state.copy()))
    state = {"items": []}
    item = {"index": 2, "title": "Fundamentos Neuropsicológicos", "progress": {}}
    tracker = downloader.ItemProgressTracker(str(tmp_path), state, item)
    tracker({"status": "downloading", "downloaded_bytes": 565, "total_bytes": 1000, "_percent_str": "0.0%"})
    assert item["progress"]["percent"] == 56.5

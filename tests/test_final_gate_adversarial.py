from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import downloader
from yt_dlp_tui.errors import ErrorKind


def _video_id(url):
    return (parse_qs(urlparse(url).query).get("v") or ["single"])[0]


class GateYDL:
    scenarios = {}
    calls = {}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

    def download(self, urls):
        video_id = _video_id(urls[0])
        count = type(self).calls.get(video_id, 0) + 1
        type(self).calls[video_id] = count
        actions = type(self).scenarios.get(video_id, ["success"])
        action = actions[min(count - 1, len(actions) - 1)]
        stage = Path(self.opts["outtmpl"]).parent
        stage.mkdir(parents=True, exist_ok=True)
        if isinstance(action, str) and action.startswith("ERROR:"):
            logger = self.opts.get("logger")
            if logger:
                logger.error(action)
            (stage / f"partial-{video_id}.part").write_bytes(b"partial")
            raise RuntimeError(action)
        payload = b"bad" * 1200 if action == "success_bad" else b"good" * 1200
        (stage / f"Video [{video_id}].m4a").write_bytes(payload)
        return 0


def _item(index, video_id):
    return {
        "index": index,
        "video_id": video_id,
        "title": f"Video {index}",
        "url": f"https://example.test/watch?v={video_id}",
        "available": True,
        "status": "pending",
        "attempts": 0,
        "retry_count": 0,
        "last_retry_at": None,
        "started_at": None,
        "completed_at": None,
        "final_file": None,
        "last_error": None,
        "last_error_kind": None,
        "audit_status": "not_run",
        "audit_at": None,
        "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
    }


def test_full_adversarial_playlist_gate(monkeypatch, tmp_path):
    items = [_item(i, f"v{i}") for i in range(1, 7)]
    state = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "Gate", "source_url": "https://example.test/?list=p"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": items,
        "audit": {"status": "not_run", "last_run_at": None, "checked": 0, "ok": 0, "failed": 0, "unavailable": 0},
    }
    task_dir = tmp_path / "Gate"
    task_dir.mkdir()

    GateYDL.calls = {}
    GateYDL.scenarios = {
        "v1": ["success"],
        "v2": ["ERROR: HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out.", "success"],
        "v3": ["ERROR: [youtube] v3: This video has been removed"],
        "v4": ["ERROR: [youtube] Sign in to confirm you're not a bot", "success"],
        "v5": ["success"],
        "v6": ["success_bad", "success"],
    }

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", GateYDL)
    monkeypatch.setattr(downloader.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(downloader, "_ffmpeg_exe", lambda: "/fake/ffmpeg")
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: {"id": "p", "title": "Gate", "entries": items})
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))

    def integrity(path, ffmpeg_exe=None):
        data = Path(path).read_bytes()
        return (data.startswith(b"good"), None if data.startswith(b"good") else "corrupt")

    monkeypatch.setattr(downloader, "_integrity_check", integrity)
    refresh_calls = []
    def refresh(reason=None, *, initial=False):
        refresh_calls.append((reason, initial))
        return True

    files = downloader._download_playlist(
        "https://example.test/?list=p", str(tmp_path), "audio", "best", refresh
    )

    assert state["status"] == "completed_with_unavailable"
    assert items[0]["status"] == "completed"
    assert items[1]["status"] == "completed"
    assert items[2]["status"] == "unavailable"
    assert items[2]["available"] is False
    assert items[2]["last_error_kind"] == ErrorKind.PERMANENT_UNAVAILABLE.value
    assert items[3]["status"] == "completed"
    assert items[4]["status"] == "completed"
    assert items[5]["status"] == "completed"
    assert state["audit"]["status"] == "passed_with_unavailable"
    assert state["audit"]["ok"] == 5
    assert state["audit"]["unavailable"] == 1

    # Completed items 1/5 were never repeated; only intended recovery paths repeat.
    assert GateYDL.calls["v1"] == 1
    assert GateYDL.calls["v2"] == 2
    assert GateYDL.calls["v3"] == 1
    assert GateYDL.calls["v4"] == 2
    assert GateYDL.calls["v5"] == 1
    assert GateYDL.calls["v6"] == 2
    assert len(refresh_calls) == 1
    assert refresh_calls[0][1] is False

    # No partial staging artifacts remain after all recovery paths.
    assert not list(task_dir.rglob("*.part"))
    assert not (task_dir / ".yt-dlp-tui-tmp").exists()
    assert len([p for p in task_dir.glob("*.m4a")]) == 5
    assert len(files) >= 5


def test_process_ended_mid_item_is_resumable_and_staging_is_cleaned(tmp_path):
    item = _item(1, "v1")
    item["status"] = "downloading"
    state = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "Gate", "source_url": "x"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": [item],
        "audit": {},
    }
    task_dir = tmp_path / "Gate"; task_dir.mkdir()
    stage = Path(downloader.stage_dir(str(task_dir), "v1"))
    stage.mkdir(parents=True)
    (stage / "Video [v1].m4a.part").write_bytes(b"partial")

    downloader._recover_incomplete_state(str(task_dir), state)

    assert item["status"] == "pending"
    assert item["progress"]["percent"] == 0.0
    assert not stage.exists()


def test_deno_missing_is_js_runtime_and_does_not_touch_auth(monkeypatch):
    monkeypatch.setattr(downloader.shutil, "which", lambda name: None if name == "deno" else "/fake/ffmpeg")
    failure = downloader._check_js_runtime()
    assert failure.kind is ErrorKind.JS_RUNTIME
    assert "Deno" in failure.technical_message


def test_ejs_missing_is_js_runtime(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "deno" if name == "deno" else "/fake/ffmpeg")
    monkeypatch.setattr(
        downloader.subprocess, "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="deno 2.9.5\n", stderr=""),
    )
    def missing(name):
        if name == "yt_dlp_ejs":
            raise ImportError("missing")
        return object()
    monkeypatch.setattr(downloader.importlib, "import_module", missing)
    failure = downloader._check_js_runtime()
    assert failure.kind is ErrorKind.JS_RUNTIME
    assert "yt-dlp-ejs" in failure.technical_message

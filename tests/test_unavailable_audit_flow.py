from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp

from yt_dlp_tui import downloader
from yt_dlp_tui.errors import ErrorKind


def _video_id(url):
    return (parse_qs(urlparse(url).query).get("v") or ["single"])[0]


class ScenarioYoutubeDL:
    scenarios = {}
    calls = {}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def download(self, urls):
        video_id = _video_id(urls[0])
        count = type(self).calls.get(video_id, 0) + 1
        type(self).calls[video_id] = count
        sequence = type(self).scenarios.get(video_id, ["success"])
        action = sequence[min(count - 1, len(sequence) - 1)]
        stage = Path(self.opts["outtmpl"]).parent
        stage.mkdir(parents=True, exist_ok=True)
        if action != "success":
            logger = self.opts.get("logger")
            if logger:
                logger.error(str(action))
            raise RuntimeError(str(action))
        ext = "m4a" if "bestaudio" in str(self.opts.get("format", "")) else "mp4"
        (stage / f"Video [{video_id}].{ext}").write_bytes(b"good" * 1200)
        return 0


@pytest.fixture(autouse=True)
def scenario(monkeypatch):
    ScenarioYoutubeDL.scenarios = {}
    ScenarioYoutubeDL.calls = {}
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", ScenarioYoutubeDL)
    monkeypatch.setattr(downloader.time, "sleep", lambda seconds: None)


def _item(index, video_id, status="pending", available=True, final_file=None):
    return {
        "index": index,
        "video_id": video_id,
        "title": f"Video {index}",
        "url": f"https://example.test/watch?v={video_id}",
        "available": available,
        "status": status,
        "attempts": 0,
        "retry_count": 0,
        "last_retry_at": None,
        "started_at": None,
        "completed_at": None,
        "final_file": final_file,
        "last_error": None,
        "last_error_kind": None,
        "audit_status": "not_run",
        "audit_at": None,
        "progress": {"percent": 100.0 if status == "completed" else 0.0, "downloaded_bytes": 0, "total_bytes": None},
    }


def _state(items):
    return {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "Playlist", "source_url": "https://example.test/?list=p"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": items,
        "audit": {"status": "not_run", "last_run_at": None, "checked": 0, "ok": 0, "failed": 0, "unavailable": 0},
    }


def _run_playlist(monkeypatch, tmp_path, state):
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir(exist_ok=True)
    metadata = {"id": "p", "title": "Playlist", "entries": state["items"]}
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: metadata)
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))
    return task_dir, downloader._download_playlist(
        "https://example.test/?list=p", str(tmp_path), "audio", "best", None
    )


def test_playlist_five_items_one_removed_finishes_with_unavailable(monkeypatch, tmp_path, capsys):
    items = [_item(i, f"v{i}") for i in range(1, 6)]
    state = _state(items)
    ScenarioYoutubeDL.scenarios = {
        "v1": ["success"],
        "v2": ["success"],
        "v3": ["ERROR: [youtube] v3: This video has been removed"],
        "v4": ["success"],
        "v5": ["success"],
    }
    monkeypatch.setattr(downloader, "_integrity_check", lambda path, ffmpeg_exe=None: (True, None))

    task_dir, files = _run_playlist(monkeypatch, tmp_path, state)
    out = capsys.readouterr().out

    assert len(files) == 4
    assert items[2]["available"] is False
    assert items[2]["status"] == "unavailable"
    assert items[2]["last_error_kind"] == ErrorKind.PERMANENT_UNAVAILABLE.value
    assert state["status"] == "completed_with_unavailable"
    assert state["audit"]["checked"] == 4
    assert state["audit"]["ok"] == 4
    assert state["audit"]["unavailable"] == 1
    assert "4/4 vídeos disponíveis íntegros" in out
    assert "1 vídeo(s) da playlist estavam indisponíveis" in out
    assert len(list(task_dir.glob("*.m4a"))) == 4


def test_private_item_has_no_network_retry_and_next_item_runs(monkeypatch, tmp_path):
    items = [_item(1, "private"), _item(2, "ok")]
    state = _state(items)
    ScenarioYoutubeDL.scenarios = {
        "private": ["ERROR: [youtube] private: This video is private"],
        "ok": ["success"],
    }
    monkeypatch.setattr(downloader, "_integrity_check", lambda path, ffmpeg_exe=None: (True, None))

    _run_playlist(monkeypatch, tmp_path, state)

    assert ScenarioYoutubeDL.calls["private"] == 1
    assert ScenarioYoutubeDL.calls["ok"] == 1
    assert items[0]["status"] == "unavailable"
    assert items[1]["status"] == "completed"


def test_timeout_is_not_converted_to_unavailable(monkeypatch, tmp_path):
    item = _item(1, "slow")
    state = _state([item])
    ScenarioYoutubeDL.scenarios = {"slow": ["HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out."]}
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()

    result = downloader._download_item_to_stage(item, str(task_dir), state, "audio", "best")

    assert result is None
    assert item["available"] is True
    assert item["status"] == "failed"
    assert item["last_error_kind"] == ErrorKind.TRANSIENT_NETWORK.value
    assert ScenarioYoutubeDL.calls["slow"] == 3


def test_missing_completed_file_returns_pending_and_is_redownloaded(monkeypatch, tmp_path):
    item = _item(1, "v1", status="completed", final_file="Video [v1].m4a")
    state = _state([item])
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()

    downloader._recover_incomplete_state(str(task_dir), state)
    assert item["status"] == "pending"
    assert item["final_file"] is None

    result = downloader._download_item_to_stage(item, str(task_dir), state, "audio", "best")
    assert result is not None
    assert Path(result).is_file()
    assert item["status"] == "completed"


def test_corrupt_completed_file_is_deleted_redownloaded_and_reaudited(monkeypatch, tmp_path):
    item = _item(1, "v1", status="completed", final_file="Old [v1].m4a")
    state = _state([item])
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()
    old = task_dir / item["final_file"]
    old.write_bytes(b"bad" * 1500)

    def integrity(path, ffmpeg_exe=None):
        data = Path(path).read_bytes()
        return (data.startswith(b"good"), None if data.startswith(b"good") else "corrupt")

    monkeypatch.setattr(downloader, "_integrity_check", integrity)
    metadata = {"id": "p", "title": "Playlist", "entries": [item]}
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: metadata)
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))

    files = downloader._download_playlist("https://example.test/?list=p", str(tmp_path), "audio", "best", None)

    assert not old.exists()
    assert len(files) == 1
    assert item["status"] == "completed"
    assert item["audit_status"] == "ok"
    assert state["audit"]["status"] == "passed"
    assert Path(task_dir / item["final_file"]).read_bytes().startswith(b"good")


def test_item_becoming_unavailable_during_repair_is_removed_from_expected_set(monkeypatch, tmp_path):
    item = _item(1, "v1", status="completed", final_file="Old [v1].m4a")
    state = _state([item])
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()
    (task_dir / item["final_file"]).write_bytes(b"bad" * 1500)
    ScenarioYoutubeDL.scenarios = {"v1": ["ERROR: [youtube] v1: This video has been removed"]}
    monkeypatch.setattr(downloader, "_integrity_check", lambda path, ffmpeg_exe=None: (False, "corrupt"))
    metadata = {"id": "p", "title": "Playlist", "entries": [item]}
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: metadata)
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))

    files = downloader._download_playlist("https://example.test/?list=p", str(tmp_path), "audio", "best", None)

    assert files == []
    assert ScenarioYoutubeDL.calls["v1"] == 1
    assert item["available"] is False
    assert item["status"] == "unavailable"
    assert state["status"] == "completed_with_unavailable"
    assert state["audit"]["checked"] == 0
    assert state["audit"]["unavailable"] == 1
    assert state["audit"]["status"] == "passed_with_unavailable"


def test_missing_flat_playlist_entry_is_unresolved_not_permanent(monkeypatch):
    class FlatYDL:
        def __init__(self, opts): self.opts = opts
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def extract_info(self, url, download=False):
            return {"id": "p", "title": "P", "entries": [None]}

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FlatYDL)
    metadata = downloader._extract_playlist("https://example.test/?list=p")
    item = metadata["entries"][0]
    assert item["available"] is True
    assert item["status"] == "unresolved"
    assert item["last_error_kind"] == ErrorKind.UNKNOWN.value


def test_unresolved_item_keeps_playlist_incomplete_and_is_not_downloaded(monkeypatch, tmp_path):
    item = _item(1, "unresolved-1")
    item.update({"url": None, "status": "unresolved", "last_error_kind": ErrorKind.UNKNOWN.value})
    state = _state([item])
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()
    metadata = {"id": "p", "title": "Playlist", "entries": [item]}
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: metadata)
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))
    monkeypatch.setattr(downloader, "_integrity_check", lambda path, ffmpeg_exe=None: (True, None))

    files = downloader._download_playlist("https://example.test/?list=p", str(tmp_path), "audio", "best", None)

    assert files == []
    assert item["available"] is True
    assert item["status"] == "unresolved"
    assert state["status"] == "incomplete"
    assert state["audit"]["failed"] == 1
    assert ScenarioYoutubeDL.calls == {}


def test_audit_never_claims_success_without_ffmpeg_or_deletes_media(monkeypatch, tmp_path):
    item = _item(1, "v1", status="completed", final_file="Video [v1].m4a")
    state = _state([item])
    task_dir = tmp_path / "Playlist"; task_dir.mkdir()
    media = task_dir / item["final_file"]
    media.write_bytes(b"good" * 1200)
    monkeypatch.setattr(downloader, "_ffmpeg_exe", lambda: None)
    with pytest.raises(RuntimeError, match="FFmpeg indisponível"):
        downloader._audit_playlist(str(task_dir), state)
    assert media.exists()
    assert state["audit"]["status"] == "blocked"
    assert state["audit"]["checked"] == 0

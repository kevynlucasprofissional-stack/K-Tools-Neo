from pathlib import Path
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import downloader


class EmptyPlaylistYDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        return {
            "id": "PL-empty-bug",
            "title": "Playlist que não é vazia",
            "playlist_count": 7,
            "entries": [],
        }


def _empty_state():
    return {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "PL-empty-bug", "title": "Playlist", "source_url": "x"},
        "mode": {"format": "video", "quality": "best"},
        "status": "in_progress",
        "items": [],
        "audit": {},
    }


def test_playlist_extraction_must_not_accept_zero_entries(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", EmptyPlaylistYDL)

    with pytest.raises(downloader.EmptyPlaylistExtractionError) as exc:
        downloader._extract_playlist("https://www.youtube.com/playlist?list=PL-empty-bug")

    assert exc.value.expected_count == 7
    assert "nenhum item" in str(exc.value).lower()


def test_audit_must_never_pass_a_playlist_with_zero_items(monkeypatch, tmp_path):
    state = _empty_state()
    monkeypatch.setattr(downloader, "_ffmpeg_exe", lambda: "/fake/ffmpeg")

    with pytest.raises(downloader.EmptyPlaylistExtractionError):
        downloader._audit_playlist(str(tmp_path), state)

    assert state["status"] == "invalid_empty_playlist"
    assert state["audit"]["status"] == "blocked_empty_playlist"


class RecoveringPlaylistYDL:
    calls = []

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        type(self).calls.append((url, dict(self.opts)))
        if len(type(self).calls) == 1:
            return {
                "id": "PL-recover",
                "title": "Recuperável",
                "playlist_count": 2,
                "entries": [],
            }
        return {
            "id": "PL-recover",
            "title": "Recuperável",
            "playlist_count": 2,
            "entries": [
                {"id": "v1", "title": "Um", "url": "v1"},
                {"id": "v2", "title": "Dois", "url": "v2"},
            ],
        }


def test_empty_playlist_is_reextracted_before_failing(monkeypatch):
    RecoveringPlaylistYDL.calls = []
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", RecoveringPlaylistYDL)
    monkeypatch.setattr(downloader.time, "sleep", lambda _: None)

    metadata = downloader._extract_playlist(
        "https://www.youtube.com/watch?v=v1&list=PL-recover&index=1"
    )

    assert [item["video_id"] for item in metadata["entries"]] == ["v1", "v2"]
    assert len(RecoveringPlaylistYDL.calls) == 2
    # Playlist extraction should strip the watch-video context and target the
    # playlist directly, reducing ambiguity in the YouTube tab extractor.
    assert RecoveringPlaylistYDL.calls[0][0] == (
        "https://www.youtube.com/watch?v=v1&list=PL-recover&index=1"
    )
    assert RecoveringPlaylistYDL.calls[1][0] == (
        "https://www.youtube.com/playlist?list=PL-recover"
    )


def test_persistent_empty_playlist_uses_bounded_fallback_strategies(monkeypatch):
    calls = []

    class AlwaysEmptyYDL(EmptyPlaylistYDL):
        def __init__(self, opts):
            super().__init__(opts)
            calls.append(dict(opts))

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", AlwaysEmptyYDL)
    monkeypatch.setattr(downloader.time, "sleep", lambda _: None)

    with pytest.raises(downloader.EmptyPlaylistExtractionError):
        downloader._extract_playlist("https://www.youtube.com/playlist?list=PL-empty-bug")

    assert len(calls) == downloader.MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS
    assert calls[0]["extract_flat"] is True
    assert calls[1]["extract_flat"] is True
    assert calls[-1]["extract_flat"] is False
    assert calls[-1]["skip_download"] is True


def test_persistent_empty_playlist_has_clear_tui_message_and_creates_no_false_task(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(downloader, "_preflight", lambda *a, **k: True)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", EmptyPlaylistYDL)
    monkeypatch.setattr(downloader.time, "sleep", lambda _: None)

    result = downloader.download_media(
        "https://www.youtube.com/playlist?list=PL-empty-bug",
        str(tmp_path),
        is_playlist=True,
        file_format="video",
        quality="best",
    )

    out = capsys.readouterr().out.lower()
    assert result == []
    assert "não consegui obter os vídeos da playlist" in out
    assert "nenhum download foi iniciado" in out
    assert "0/0" not in out
    assert not list(tmp_path.rglob("YT-DLP-TUI-controle.json"))


def test_old_zero_item_false_success_control_is_repopulated_when_extraction_recovers(tmp_path):
    metadata = {
        "id": "PL-old-empty",
        "title": "Playlist Recuperada",
        "entries": [
            {
                "index": 1,
                "video_id": "v1",
                "title": "Um",
                "url": "https://www.youtube.com/watch?v=v1",
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
        ],
    }
    task_dir = tmp_path / "Playlist_Recuperada"
    task_dir.mkdir()
    stale = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "PL-old-empty", "title": "Playlist Recuperada", "source_url": "x"},
        "mode": {"format": "video", "quality": "best"},
        "status": "completed",
        "items": [],
        "audit": {"status": "passed", "last_run_at": None, "checked": 0, "ok": 0, "failed": 0, "unavailable": 0},
    }
    downloader.save_control(str(task_dir), stale)

    resolved_dir, state = downloader._prepare_playlist_state(
        str(tmp_path), metadata, "https://www.youtube.com/playlist?list=PL-old-empty", "video", "best"
    )

    assert Path(resolved_dir) == task_dir
    assert len(state["items"]) == 1
    assert state["items"][0]["video_id"] == "v1"
    assert state["status"] == "in_progress"


def test_valid_playlist_does_not_consume_empty_playlist_fallback_budget(monkeypatch):
    calls = []

    class ValidYDL:
        def __init__(self, opts):
            calls.append(dict(opts))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=False):
            return {
                "id": "PL-ok",
                "title": "OK",
                "playlist_count": 1,
                "entries": [{"id": "v1", "title": "Um", "url": "v1"}],
            }

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", ValidYDL)
    metadata = downloader._extract_playlist("https://www.youtube.com/playlist?list=PL-ok")

    assert len(metadata["entries"]) == 1
    assert len(calls) == 1
    assert calls[0]["extract_flat"] is True
    assert "skip_download" not in calls[0]

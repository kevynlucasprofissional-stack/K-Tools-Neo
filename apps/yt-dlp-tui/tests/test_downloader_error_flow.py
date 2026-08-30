import importlib
import sys
import types
from pathlib import Path

import pytest


# The execution environment used by these deterministic tests does not need the
# real yt-dlp package.  Provide only the import surface downloader.py requires;
# each test replaces YoutubeDL with the desired failure scenario.
if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp


downloader = importlib.import_module("yt_dlp_tui.downloader")


class FailingYoutubeDL:
    message = "failure"
    logger_messages = ()

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def download(self, urls):
        logger = self.opts.get("logger")
        for level, message in self.logger_messages:
            getattr(logger, level)(message)
        raise RuntimeError(self.message)


class AuthFailingYoutubeDL(FailingYoutubeDL):
    message = "ERROR: [youtube] x: Sign in to confirm you're not a bot"
    logger_messages = (("error", message),)


class JsFailingYoutubeDL(FailingYoutubeDL):
    message = "ERROR: [youtube] x: The page needs to be reloaded."
    logger_messages = (
        ("warning", "n challenge solving failed; JavaScript runtime/challenge solver required"),
        ("error", message),
    )


class TimeoutFailingYoutubeDL(FailingYoutubeDL):
    message = "HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out."
    logger_messages = (("error", message),)


def test_single_auth_failure_is_presented_only_after_classification(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", AuthFailingYoutubeDL)
    result = downloader._download_single("https://example.test", str(tmp_path), "audio", "best", None)
    out = capsys.readouterr().out

    assert result == []
    assert "Sua sessão do YouTube precisa ser renovada" in out
    assert "Sign in to confirm" not in out
    assert "Error: ERROR:" not in out


def test_single_js_failure_does_not_trigger_auth(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", JsFailingYoutubeDL)
    callback_calls = []

    result = downloader._download_single(
        "https://example.test", str(tmp_path), "audio", "best", lambda reason: callback_calls.append(reason) or False
    )
    out = capsys.readouterr().out

    assert result == []
    assert callback_calls == []
    assert "resolvedor JavaScript" in out
    assert "Error: ERROR:" not in out


def test_playlist_item_retries_transient_network_then_records_exhaustion(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", TimeoutFailingYoutubeDL)
    task_dir = tmp_path / "playlist"
    task_dir.mkdir()
    item = {
        "index": 1,
        "video_id": "abc",
        "title": "Example",
        "url": "https://example.test/watch?v=abc",
        "available": True,
        "status": "pending",
        "attempts": 0,
        "started_at": None,
        "completed_at": None,
        "final_file": None,
        "last_error": None,
        "last_error_kind": None,
        "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
    }
    state = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "P", "source_url": "https://example.test"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": [item],
        "audit": {},
    }

    monkeypatch.setattr(downloader.time, "sleep", lambda seconds: None)
    result = downloader._download_item_to_stage(item, str(task_dir), state, "audio", "best")
    out = capsys.readouterr().out

    assert result is None
    assert item["status"] == "failed"
    assert item["attempts"] == 3
    assert item["retry_count"] == 2
    assert item["last_error_kind"] == "transient_network"
    assert "Read timed out" in item["last_error"]
    assert "continuou instável após 3 tentativas" in out
    assert "Error: ERROR:" not in out

class JsExtractFailingYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        logger = self.opts.get("logger")
        logger.warning("n challenge solving failed; JavaScript runtime/challenge solver required")
        logger.error("ERROR: [youtube] x: The page needs to be reloaded.")
        raise RuntimeError("The page needs to be reloaded.")


def test_playlist_extraction_preserves_js_classification_context(monkeypatch):
    from yt_dlp_tui.errors import ClassifiedFailureError, ErrorKind

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", JsExtractFailingYoutubeDL)
    with pytest.raises(ClassifiedFailureError) as exc_info:
        downloader._extract_playlist("https://example.test/playlist?list=x")

    assert exc_info.value.classification.kind is ErrorKind.JS_RUNTIME
    assert "n challenge solving failed" in exc_info.value.classification.technical_message

class PrivateFailingYoutubeDL(FailingYoutubeDL):
    message = "ERROR: [youtube] abc: This video is private"
    logger_messages = (("error", message),)


def test_playlist_item_permanent_unavailable_is_marked_and_not_retried(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", PrivateFailingYoutubeDL)
    task_dir = tmp_path / "playlist-private"
    task_dir.mkdir()
    item = {
        "index": 1,
        "video_id": "abc",
        "title": "Private",
        "url": "https://example.test/watch?v=abc",
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
        "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
    }
    state = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "P", "source_url": "https://example.test"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": [item],
        "audit": {},
    }

    result = downloader._download_item_to_stage(item, str(task_dir), state, "audio", "best")

    assert result is None
    assert item["available"] is False
    assert item["status"] == "unavailable"
    assert item["attempts"] == 1
    assert item["retry_count"] == 0
    assert item["last_error_kind"] == "permanent_unavailable"
    assert "private" in item["last_error"].lower()

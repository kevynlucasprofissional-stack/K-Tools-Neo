import os
from pathlib import Path
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import cli, control, downloader


def test_cleanup_stage_never_follows_symlinked_temp_root(tmp_path):
    task = tmp_path / "task"
    outside = tmp_path / "outside"
    task.mkdir(); outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    link = task / control.TEMP_DIRNAME
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink não suportado neste ambiente")

    control.cleanup_stage(str(task), "video")
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not os.path.lexists(link)


def test_safe_delete_rejects_outside_path(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside.txt"; outside.write_text("keep", encoding="utf-8")
    assert downloader._safe_delete(str(outside), str(root)) is False
    assert outside.exists()


def test_safe_delete_unlinks_symlink_without_deleting_target(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    sentinel = outside / "keep.txt"; sentinel.write_text("keep", encoding="utf-8")
    link = root / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink não suportado neste ambiente")
    assert downloader._safe_delete(str(link), str(root)) is True
    assert sentinel.exists()
    assert not os.path.lexists(link)


def test_rename_rejects_path_escape(monkeypatch, tmp_path, capsys):
    media = tmp_path / "video.mp4"; media.write_bytes(b"x")
    monkeypatch.setattr("builtins.input", lambda prompt="": "../fora")
    cli._rename_file(str(media))
    assert media.exists()
    assert not (tmp_path.parent / "fora.mp4").exists()
    assert "nome inválido" in capsys.readouterr().out


def test_control_final_file_cannot_escape_task_directory(monkeypatch, tmp_path):
    task = tmp_path / "task"; task.mkdir()
    outside = tmp_path / "outside.m4a"; outside.write_bytes(b"good" * 1200)
    state = {
        "schema_version": 3,
        "task_type": "playlist",
        "playlist": {"id": "p", "title": "P", "source_url": "x"},
        "mode": {"format": "audio", "quality": "best"},
        "status": "in_progress",
        "items": [{
            "index": 1, "video_id": "v1", "title": "V", "url": "https://example.test/watch?v=v1",
            "available": True, "status": "completed", "attempts": 1,
            "retry_count": 0, "last_retry_at": None, "started_at": None, "completed_at": None,
            "final_file": "../outside.m4a", "last_error": None, "last_error_kind": None,
            "audit_status": "not_run", "audit_at": None,
            "progress": {"percent": 100.0, "downloaded_bytes": 0, "total_bytes": None},
        }],
        "audit": {},
    }
    downloader._recover_incomplete_state(str(task), state)
    item = state["items"][0]
    assert outside.exists()
    assert item["status"] == "pending"
    assert item["final_file"] is None
    assert item["last_error_kind"] == downloader.ErrorKind.LOCAL_IO.value


def test_existing_media_symlink_outside_task_is_not_trusted(tmp_path):
    task = tmp_path / "task"; task.mkdir()
    outside = tmp_path / "outside.m4a"; outside.write_bytes(b"x" * 4096)
    link = task / "Video [v1].m4a"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink não suportado neste ambiente")

    assert downloader._find_existing_final_by_id(str(task), "v1") is None
    assert outside.exists()

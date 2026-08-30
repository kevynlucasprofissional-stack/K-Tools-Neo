from pathlib import Path
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import cli, downloader


def _run_tui(monkeypatch, tmp_path, inputs):
    answers = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(cli.os, "system", lambda *a, **k: 0)
    return str(tmp_path)


def test_audio_download_options_remain_supported(tmp_path):
    opts = downloader._build_download_opts(str(tmp_path), "audio", "best", None, downloader.CaptureLogger())
    assert "bestaudio" in opts["format"]
    assert opts["continuedl"] is False
    assert opts["nopart"] is False


@pytest.mark.parametrize(
    ("quality", "fragment"),
    [("480", "height<=480"), ("720", "height<=720"), ("1080", "height<=1080"), ("best", "bv*[ext=mp4]")],
)
def test_video_quality_options_remain_supported(tmp_path, quality, fragment):
    opts = downloader._build_download_opts(str(tmp_path), "video", quality, None, downloader.CaptureLogger())
    assert fragment in opts["format"]
    assert opts["merge_output_format"] == "mp4"


def test_tui_default_audio_single_link(monkeypatch, tmp_path):
    calls = []
    target = _run_tui(monkeypatch, tmp_path, ["https://example.test/video", "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: calls.append((url, kw)) or [])
    cli.interactive_mode(target)
    assert calls[0][0] == "https://example.test/video"
    assert calls[0][1]["file_format"] == "audio"
    assert calls[0][1]["quality"] == "best"


@pytest.mark.parametrize(("selection", "quality"), [("1", "480"), ("2", "720"), ("3", "1080"), ("4", "best")])
def test_tui_video_resolution_commands(monkeypatch, tmp_path, selection, quality):
    calls = []
    target = _run_tui(monkeypatch, tmp_path, ["video", "res", selection, "https://example.test/video", "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: calls.append(kw) or [])
    cli.interactive_mode(target)
    assert calls[0]["file_format"] == "video"
    assert calls[0]["quality"] == quality


def test_search_s_downloads_top_result(monkeypatch, tmp_path):
    calls = []
    target = _run_tui(monkeypatch, tmp_path, ["s:teste", "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: calls.append((url, kw)) or [])
    cli.interactive_mode(target)
    assert calls[0][0] == "ytsearch1:teste"


@pytest.mark.parametrize(("prefix", "count"), [("s3", 3), ("s5", 5)])
def test_search_pick_commands(monkeypatch, tmp_path, prefix, count):
    calls = []
    results = [
        {"id": f"v{i}", "title": f"V{i}", "duration": 10, "uploader": "Canal"}
        for i in range(1, count + 1)
    ]
    target = _run_tui(monkeypatch, tmp_path, [f"{prefix}:teste", "2", "q"])
    monkeypatch.setattr(cli, "fetch_search_results", lambda query, n, **kw: results)
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: calls.append(url) or [])
    cli.interactive_mode(target)
    assert calls == ["https://www.youtube.com/watch?v=v2"]


def test_txt_bulk_downloads_each_nonempty_link(monkeypatch, tmp_path):
    links = tmp_path / "lista.txt"
    links.write_text("https://example.test/1\n\nhttps://example.test/2\n", encoding="utf-8")
    calls = []
    target = _run_tui(monkeypatch, tmp_path, [str(links), "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: calls.append(url) or [])
    cli.interactive_mode(target)
    assert calls == ["https://example.test/1", "https://example.test/2"]


def test_open_command_opens_selected_run_folder(monkeypatch, tmp_path):
    opened = []
    target = _run_tui(monkeypatch, tmp_path, ["open", "q"])
    monkeypatch.setattr(cli.os, "startfile", lambda path: opened.append(path), raising=False)
    cli.interactive_mode(target)
    assert opened == [str(tmp_path)]


def test_rename_single_stays_in_same_directory(monkeypatch, tmp_path):
    media = tmp_path / "Video [v1].m4a"
    media.write_bytes(b"x")
    target = _run_tui(monkeypatch, tmp_path, ["rename", "https://example.test/video", "Novo Nome", "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: [str(media)])
    cli.interactive_mode(target)
    assert not media.exists()
    assert (tmp_path / "Novo Nome.m4a").exists()


def test_rename_is_not_applied_to_playlist_controlled_result(monkeypatch, tmp_path, capsys):
    media = tmp_path / "Video [v1].m4a"
    media.write_bytes(b"x")
    target = _run_tui(monkeypatch, tmp_path, ["rename", "https://example.test/watch?v=v1&list=p", "q"])
    monkeypatch.setattr(cli, "smart_download", lambda url, **kw: [str(media)])
    cli.interactive_mode(target)
    assert media.exists()
    assert "apenas a vídeos individuais" in capsys.readouterr().out

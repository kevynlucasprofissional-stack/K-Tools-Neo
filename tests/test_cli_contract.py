import importlib
import sys
import types


if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp

cli = importlib.import_module("yt_dlp_tui.cli")


def test_every_interactive_run_requires_folder_selection(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["yt-dlp-tui"])
    monkeypatch.setattr(cli, "_select_output_folder", lambda: calls.append("picker") or None)
    monkeypatch.setattr(cli, "interactive_mode", lambda target: calls.append(("interactive", target)))

    cli.main()
    assert calls == ["picker"]


def test_selected_folder_is_session_only_and_passed_to_tui(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(sys, "argv", ["yt-dlp-tui"])
    monkeypatch.setattr(cli, "_select_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(cli, "interactive_mode", lambda target: calls.append(target))

    cli.main()
    assert calls == [str(tmp_path)]


def test_manual_cache_command_uses_manual_import_flow(monkeypatch, tmp_path):
    inputs = iter(["cache", "q"])
    modes = []
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr(cli.os, "system", lambda *a, **k: 0)
    monkeypatch.setattr(cli, "refresh_cookie_interactive", lambda *a, **k: modes.append(k) or True)

    cli.interactive_mode(str(tmp_path))
    assert modes == [{"manual": True}]

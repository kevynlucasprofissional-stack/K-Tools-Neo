from pathlib import Path
import sys
import types

if "yt_dlp" not in sys.modules:
    fake = types.ModuleType("yt_dlp")
    fake.YoutubeDL = object
    sys.modules["yt_dlp"] = fake

from yt_dlp_tui import downloader


def test_download_template_uses_youtube_title_without_video_id(tmp_path):
    opts = downloader._build_download_opts(str(tmp_path), "video", "best", None, downloader.CaptureLogger())
    assert opts["outtmpl"].endswith("%(title)s.%(ext)s")
    assert "%(id)s" not in opts["outtmpl"]
    assert opts["restrictfilenames"] is False


def test_title_only_file_can_be_recovered_by_playlist_title(tmp_path):
    media = tmp_path / "[Curso] Terapia do Esquema #01 - Pressupostos Básicos.mp4"
    media.write_bytes(b"x" * 4096)
    item = {
        "video_id": "mZ0BKqlDNfE",
        "title": "[Curso] Terapia do Esquema #01 - Pressupostos Básicos",
    }
    assert downloader._find_existing_final_for_item(str(tmp_path), item) == str(media)


def test_legacy_id_filename_is_still_recoverable(tmp_path):
    media = tmp_path / "Curso_Terapia_01 [mZ0BKqlDNfE].mp4"
    media.write_bytes(b"x" * 4096)
    item = {"video_id": "mZ0BKqlDNfE", "title": "Outro título"}
    assert downloader._find_existing_final_for_item(str(tmp_path), item) == str(media)


def test_duplicate_titles_are_disambiguated_without_overwriting_first_file(tmp_path):
    staged = tmp_path / ".stage" / "Mesmo título.mp4"
    staged.parent.mkdir()
    staged.write_bytes(b"x")
    first = {"video_id": "a", "final_file": "Mesmo título.mp4"}
    second = {"video_id": "b", "final_file": None}
    state = {"items": [first, second]}
    destination = downloader._final_destination(str(tmp_path), str(staged), state, second)
    assert Path(destination).name == "Mesmo título (2).mp4"

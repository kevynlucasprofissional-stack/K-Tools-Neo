from __future__ import annotations

import http.cookiejar
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

import yt_dlp


def resolve_ffmpeg() -> str | None:
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    return None


def detect_js_runtimes() -> dict[str, dict]:
    runtimes = {}
    if shutil.which("node"):
        runtimes["node"] = {}
    if shutil.which("deno"):
        runtimes["deno"] = {}
    return runtimes


class YtDlpAdapter:
    """Encapsulates yt-dlp parameter generation and execution boundaries."""

    def __init__(self, ffmpeg_path: str | None = None):
        self._ffmpeg_path = ffmpeg_path or resolve_ffmpeg()
        self._js_runtimes = detect_js_runtimes()

    def build_options(
        self,
        media_type: str = "video",
        quality: str = "best",
        audio_format: str = "m4a",
        output_dir: Path | str | None = None,
        cookiejar: http.cookiejar.CookieJar | None = None,
        quiet: bool = True,
        simulate: bool = False,
    ) -> dict[str, Any]:
        out_dir = Path(output_dir) if output_dir else Path.cwd()
        out_template = str(out_dir / "%(playlist_index&{:03d} - |)s%(title).150B [%(id)s].%(ext)s")

        opts: dict[str, Any] = {
            "outtmpl": out_template,
            "quiet": quiet,
            "no_warnings": quiet,
            "simulate": simulate,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "restrictfilenames": False,
            "retries": 3,
            "fragment_retries": 3,
        }

        if self._ffmpeg_path:
            opts["ffmpeg_location"] = self._ffmpeg_path

        if self._js_runtimes:
            opts["js_runtimes"] = dict(self._js_runtimes)

        # Media and format selection
        if media_type.lower() == "audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format.lower(),
                    "preferredquality": "0",  # best VBR or source
                }
            ]
        else:
            # Video quality selection
            q = quality.lower().strip()
            if q == "2160p":
                opts["format"] = "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best"
            elif q == "1440p":
                opts["format"] = "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best"
            elif q == "1080p":
                opts["format"] = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            elif q == "720p":
                opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            else:
                opts["format"] = "bestvideo+bestaudio/best"

            # Merge to mp4 or mkv
            opts["merge_output_format"] = "mp4"

        return opts

    def run_download(
        self,
        url: str,
        opts: dict[str, Any],
        cookiejar: http.cookiejar.CookieJar | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        downloaded_paths: list[str] = []

        def _progress_hook(d: dict[str, Any]) -> None:
            if d.get("status") == "finished":
                filename = d.get("filename")
                if filename and os.path.isfile(filename) and filename not in downloaded_paths:
                    downloaded_paths.append(str(Path(filename).resolve()))

        run_opts = dict(opts)
        run_opts["progress_hooks"] = [_progress_hook]

        with yt_dlp.YoutubeDL(run_opts) as ydl:
            if cookiejar:
                for c in cookiejar:
                    ydl.cookiejar.set_cookie(c)
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Nenhum metadado retornado para a URL.")

            # If progress hook didn't capture (e.g. fast audio transcode), find generated file
            if not downloaded_paths:
                requested = info.get("requested_downloads")
                if requested:
                    for req in requested:
                        fn = req.get("filepath")
                        if fn and os.path.isfile(fn):
                            downloaded_paths.append(str(Path(fn).resolve()))

            return info, downloaded_paths

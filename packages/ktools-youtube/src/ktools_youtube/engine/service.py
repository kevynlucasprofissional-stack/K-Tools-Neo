from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from ..auth.base import AuthState
from ..auth.manager import YouTubeAuthManager
from .adapter import YtDlpAdapter
from .errors import (
    AuthRequiredError,
    AgeRestrictedError,
    PrivateVideoError,
    PoTokenRequiredError,
    normalize_ytdlp_error,
)


@dataclass
class YouTubeDownloadResult:
    files: list[str]
    folder: str
    metadata: dict[str, Any]
    auth_used: bool = False


def default_download_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("USERPROFILE") or os.environ.get("LOCALAPPDATA") or str(Path.home())
        p = Path(base) / "Downloads" / "K-Tools-YouTube"
    else:
        p = Path.home() / "Downloads" / "K-Tools-YouTube"
    p.mkdir(parents=True, exist_ok=True)
    return p


class YouTubeDownloadService:
    """Orchestrates public vs authenticated downloads and metadata normalization."""

    def __init__(
        self,
        auth_manager: YouTubeAuthManager | None = None,
        adapter: YtDlpAdapter | None = None,
    ):
        self._auth_manager = auth_manager or YouTubeAuthManager()
        self._adapter = adapter or YtDlpAdapter()

    def download(
        self,
        url: str,
        media_type: str = "video",
        quality: str = "best",
        audio_format: str = "m4a",
        output_dir: Path | str | None = None,
        use_auth: bool | None = None,
    ) -> YouTubeDownloadResult:
        out_dir = Path(output_dir) if output_dir else default_download_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        opts = self._adapter.build_options(
            media_type=media_type,
            quality=quality,
            audio_format=audio_format,
            output_dir=out_dir,
        )

        cookiejar = None
        auth_used = False

        # If user explicitly requested auth, or if we have an active session and use_auth is True:
        if use_auth is True:
            cookiejar = self._auth_manager.get_cookiejar()
            auth_used = cookiejar is not None

        # --- LAYER 1: Attempt download (without cookies by default) ---
        try:
            info, files = self._adapter.run_download(url, opts, cookiejar=cookiejar)
            return self._build_result(info, files, out_dir, auth_used=auth_used)
        except Exception as exc:
            norm_err = normalize_ytdlp_error(exc)

            # Check if error indicates authentication boundary and we haven't tried cookies yet
            is_auth_error = isinstance(
                norm_err,
                (AuthRequiredError, AgeRestrictedError, PrivateVideoError, PoTokenRequiredError),
            )
            if is_auth_error and not auth_used:
                # Check if AuthManager has an active session ready
                state = self._auth_manager.get_state()
                if state == AuthState.ACTIVE:
                    cookiejar = self._auth_manager.get_cookiejar()
                    if cookiejar:
                        try:
                            info, files = self._adapter.run_download(url, opts, cookiejar=cookiejar)
                            return self._build_result(info, files, out_dir, auth_used=True)
                        except Exception as retry_exc:
                            raise normalize_ytdlp_error(retry_exc) from retry_exc

            # Re-raise normalized error
            raise norm_err from exc

    def _build_result(
        self,
        info: dict[str, Any],
        files: list[str],
        folder: Path,
        auth_used: bool,
    ) -> YouTubeDownloadResult:
        is_playlist = "entries" in info
        metadata: dict[str, Any] = {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "channel": info.get("channel"),
            "duration": info.get("duration"),
            "is_playlist": is_playlist,
            "auth_used": auth_used,
        }

        if is_playlist:
            entries = info.get("entries") or []
            metadata["playlist_count"] = len(entries)
            metadata["items"] = [
                {"id": e.get("id"), "title": e.get("title"), "duration": e.get("duration")}
                for e in entries
                if e
            ]

        return YouTubeDownloadResult(
            files=files,
            folder=str(folder.resolve()),
            metadata=metadata,
            auth_used=auth_used,
        )

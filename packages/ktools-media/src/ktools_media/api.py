from __future__ import annotations

from pathlib import Path

from .audio.extract import MediaExtractionError, extract_audio_from_video

__all__ = ["extract_audio_from_video", "MediaExtractionError"]

"""Official YouTube capability package for K-Tools Neo."""

from .engine.service import YouTubeDownloadService, YouTubeDownloadResult
from .auth.manager import YouTubeAuthManager, AuthState

__all__ = [
    "YouTubeDownloadService",
    "YouTubeDownloadResult",
    "YouTubeAuthManager",
    "AuthState",
]

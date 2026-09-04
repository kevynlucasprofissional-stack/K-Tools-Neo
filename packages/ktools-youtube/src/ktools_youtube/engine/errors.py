from __future__ import annotations


class YouTubeError(Exception):
    """Base error for YouTube operations in K-Tools Neo."""

    def __init__(self, message: str, code: str = "YTDLP_ERROR", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class AuthRequiredError(YouTubeError):
    def __init__(self, message: str = "Este vídeo exige login para ser acessado.", details: dict | None = None):
        super().__init__(message, code="AUTH_REQUIRED", details=details)


class ReauthRequiredError(YouTubeError):
    def __init__(self, message: str = "Sua sessão expirou ou o Google exigiu re-login.", details: dict | None = None):
        super().__init__(message, code="REAUTH_REQUIRED", details=details)


class PrivateVideoError(YouTubeError):
    def __init__(self, message: str = "Este vídeo é privado e você não possui permissão.", details: dict | None = None):
        super().__init__(message, code="PRIVATE_VIDEO", details=details)


class VideoUnavailableError(YouTubeError):
    def __init__(self, message: str = "O vídeo ou playlist não está disponível.", details: dict | None = None):
        super().__init__(message, code="VIDEO_UNAVAILABLE", details=details)


class AgeRestrictedError(YouTubeError):
    def __init__(self, message: str = "Este vídeo possui restrição de idade (18+).", details: dict | None = None):
        super().__init__(message, code="AGE_RESTRICTED", details=details)


class GeoBlockedError(YouTubeError):
    def __init__(self, message: str = "Este vídeo não está disponível na sua região.", details: dict | None = None):
        super().__init__(message, code="GEO_BLOCKED", details=details)


class PlaylistUnavailableError(YouTubeError):
    def __init__(self, message: str = "A playlist não existe ou está inacessível.", details: dict | None = None):
        super().__init__(message, code="PLAYLIST_UNAVAILABLE", details=details)


class NetworkError(YouTubeError):
    def __init__(self, message: str = "Falha de conexão com os servidores do YouTube.", details: dict | None = None):
        super().__init__(message, code="NETWORK_ERROR", details=details)


class FFmpegRequiredError(YouTubeError):
    def __init__(self, message: str = "FFmpeg é necessário para converter ou unir as faixas.", details: dict | None = None):
        super().__init__(message, code="FFMPEG_REQUIRED", details=details)


class JsRuntimeRequiredError(YouTubeError):
    def __init__(self, message: str = "Um runtime JavaScript (Node ou Deno) é necessário para resolver os desafios do YouTube.", details: dict | None = None):
        super().__init__(message, code="JS_RUNTIME_REQUIRED", details=details)


class PoTokenRequiredError(YouTubeError):
    def __init__(self, message: str = "O YouTube exigiu um Proof of Origin Token (PO-Token) para esta solicitação.", details: dict | None = None):
        super().__init__(message, code="PO_TOKEN_REQUIRED", details=details)


def normalize_ytdlp_error(exc: Exception) -> YouTubeError:
    """Classifies yt-dlp exceptions into structured, user-friendly domain errors."""
    if isinstance(exc, YouTubeError):
        return exc

    msg = str(exc).lower()

    if "sign in to confirm your age" in msg or "age-restricted" in msg or "confirm you're 18" in msg:
        return AgeRestrictedError(str(exc))

    if "sign in to confirm you're not a bot" in msg or "bot" in msg or "sabr" in msg:
        return PoTokenRequiredError(str(exc))

    if "private video" in msg:
        return PrivateVideoError(str(exc))

    if "login required" in msg or "this video is only available to" in msg or "join this channel" in msg:
        return AuthRequiredError(str(exc))

    if "cookies" in msg and ("expired" in msg or "invalid" in msg or "re-login" in msg):
        return ReauthRequiredError(str(exc))

    if "not available in your country" in msg or "blocked in your country" in msg or "geo" in msg:
        return GeoBlockedError(str(exc))

    if "playlist does not exist" in msg or "playlist is private" in msg:
        return PlaylistUnavailableError(str(exc))

    if "this video is unavailable" in msg or "video has been removed" in msg:
        return VideoUnavailableError(str(exc))

    if (
        "connection reset" in msg
        or "timed out" in msg
        or "name or service not known" in msg
        or "getaddrinfo" in msg
        or "urlopen" in msg
        or "network" in msg
    ):
        return NetworkError(str(exc))

    if "ffmpeg is not installed" in msg or "ffprobe is not installed" in msg:
        return FFmpegRequiredError(str(exc))

    return YouTubeError(str(exc), code="YTDLP_ERROR", details={"raw_exception": type(exc).__name__})

"""Central failure classification for YT-DLP TUI.

This module deliberately separates *classification* from *policy*.  It tells the
rest of the application what kind of failure happened and whether it is
intrinsically retryable, but it does not perform retries, refresh cookies, or
change playlist state by itself.
"""

from __future__ import annotations

import errno
import http.client
import re
import socket
import urllib.error
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ErrorKind(str, Enum):
    AUTH_EXPIRED = "auth_expired"
    TRANSIENT_NETWORK = "transient_network"
    RATE_LIMIT = "rate_limit"
    PERMANENT_UNAVAILABLE = "permanent_unavailable"
    JS_RUNTIME = "js_runtime"
    LOCAL_IO = "local_io"
    FORMAT_CONFIG = "format_config"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureClassification:
    kind: ErrorKind
    retryable: bool
    user_message: str
    technical_message: str
    http_status: int | None = None


class ClassifiedFailureError(RuntimeError):
    """Carry an already-classified failure across layers without losing context."""

    def __init__(self, classification: FailureClassification):
        self.classification = classification
        super().__init__(classification.technical_message)


class CaptureLogger:
    """yt-dlp logger that captures diagnostics without printing raw errors.

    Presentation belongs to the TUI *after* classification.  This prevents a
    long yt-dlp error from leaking into the normal interface before the app has
    decided whether it is auth, network, JS-runtime, local I/O, etc.
    """

    def __init__(self):
        self.messages: list[str] = []

    def _capture(self, msg):
        if msg:
            self.messages.append(str(msg))

    def debug(self, msg):
        self._capture(msg)

    def info(self, msg):
        self._capture(msg)

    def warning(self, msg):
        self._capture(msg)

    def error(self, msg):
        self._capture(msg)

    def joined(self) -> str:
        return "\n".join(self.messages)


# Text is intentionally a fallback.  Strong structural evidence (exception
# types, causes, preserved exc_info, HTTP status) is inspected first.
_JS_MARKERS = (
    "n challenge solving failed",
    "signature solving failed",
    "javascript runtime",
    "javascript challenge",
    "challenge solver",
    "challenge solving",
    "yt-dlp-ejs",
    "ejs",
    "jsc:",
)

_AUTH_MARKERS = (
    "sign in to confirm you're not a bot",
    "sign in to confirm you’re not a bot",
    "cookies are no longer valid",
    "cookie is no longer valid",
    "authentication required",
    "please sign in",
    "login required",
)

_PERMANENT_MARKERS = (
    "video is private",
    "this video is private",
    "private video",
    "video has been removed",
    "this video has been removed",
    "video was removed",
    "this video does not exist",
    "this video is no longer available",
    "video is no longer available",
    "this video has been deleted",
    "video has been deleted",
)

_FORMAT_MARKERS = (
    "requested format is not available",
    "requested format not available",
    "no video formats found",
    "only images are available for download",
    "unsupported url",
)

_NETWORK_MARKERS = (
    "read timed out",
    "read timeout",
    "connect timed out",
    "connect timeout",
    "connection timed out",
    "connection reset",
    "connection aborted",
    "remote end closed connection",
    "remote disconnected",
    "incomplete read",
    "temporary failure in name resolution",
    "name or service not known",
    "temporary failure in name resolution",
    "unexpected_eof_while_reading",
    "ssl: unexpected eof",
    "eof occurred in violation of protocol",
    "tlsv1 alert internal error",
)

_RATE_LIMIT_MARKERS = (
    "too many requests",
    "rate limit exceeded",
    "rate limited",
    "rate-limit",
    "request throttled",
    "requests throttled",
)

_CDN_REEXTRACT_MARKERS = (
    "googlevideo.com",
    "signed url",
    "signed media url",
    "media url expired",
    "url expired",
)

_LOCAL_ERRNOS = {
    errno.EACCES,
    errno.EPERM,
    errno.ENOSPC,
    errno.EROFS,
    errno.EDQUOT,
    errno.EMFILE,
    errno.ENFILE,
}

_TRANSIENT_HTTP = {408, 425, 500, 502, 503, 504}

_MESSAGES = {
    ErrorKind.AUTH_EXPIRED: "Sua sessão do YouTube precisa ser renovada.",
    ErrorKind.TRANSIENT_NETWORK: "A conexão com o YouTube falhou temporariamente.",
    ErrorKind.RATE_LIMIT: "O YouTube limitou temporariamente as requisições.",
    ErrorKind.PERMANENT_UNAVAILABLE: "Este vídeo não está disponível para download.",
    ErrorKind.JS_RUNTIME: "O resolvedor JavaScript do YouTube precisa de atenção.",
    ErrorKind.LOCAL_IO: "Não foi possível acessar ou gravar um arquivo local.",
    ErrorKind.FORMAT_CONFIG: "O formato solicitado ou a configuração não pôde ser usada.",
    ErrorKind.UNKNOWN: "O download falhou por um motivo não reconhecido.",
}


def _unique_objects(values: Iterable[object]):
    seen: set[int] = set()
    for value in values:
        if value is None:
            continue
        identity = id(value)
        if identity in seen:
            continue
        seen.add(identity)
        yield value


def _exception_chain(error: BaseException | None):
    """Yield the wrapper plus preserved causes/exc_info without looping."""
    if error is None:
        return []

    queue: list[object] = [error]
    result: list[object] = []
    seen: set[int] = set()

    while queue:
        current = queue.pop(0)
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        result.append(current)

        for attr in ("cause", "__cause__", "__context__"):
            child = getattr(current, attr, None)
            if isinstance(child, BaseException):
                queue.append(child)

        exc_info = getattr(current, "exc_info", None)
        if isinstance(exc_info, tuple) and len(exc_info) >= 2 and isinstance(exc_info[1], BaseException):
            queue.append(exc_info[1])

    return result


def _http_status(value) -> int | None:
    for attr in ("status", "code"):
        status = getattr(value, attr, None)
        if isinstance(status, int):
            return status

    response = getattr(value, "response", None)
    status = getattr(response, "status", None)
    return status if isinstance(status, int) else None




def _http_status_from_text(text: str) -> int | None:
    match = re.search(r"\bHTTP(?:\s+Error)?\s+(\d{3})\b", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None

def _class_names(value) -> set[str]:
    try:
        return {cls.__name__ for cls in type(value).mro()}
    except Exception:
        return {type(value).__name__}


def _looks_like_yt_dlp_transport(value) -> bool:
    names = _class_names(value)
    return bool(names & {
        "TransportError",
        "IncompleteRead",
        "SSLError",
        "CertificateVerifyError",
        "ProxyError",
        "RequestError",
        "ReadTimeout",
        "ReadTimeoutError",
        "ConnectTimeout",
        "ConnectTimeoutError",
        "ProtocolError",
        "NewConnectionError",
        "RemoteDisconnected",
    })


def _technical_text(error: BaseException | None, logger_messages=None) -> str:
    pieces: list[str] = []
    for value in _exception_chain(error):
        text = str(value).strip()
        label = type(value).__name__
        if text:
            pieces.append(f"{label}: {text}")
        else:
            pieces.append(label)

    if logger_messages:
        if isinstance(logger_messages, str):
            pieces.append(logger_messages.strip())
        else:
            pieces.extend(str(m).strip() for m in logger_messages if m)

    deduped: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        if not piece or piece in seen:
            continue
        seen.add(piece)
        deduped.append(piece)

    technical = "\n".join(deduped).strip() or "erro sem detalhes"
    # Keep diagnostics useful in control.json without allowing unbounded logger
    # output to bloat the file.  The most recent tail is usually the actionable
    # part of yt-dlp's message stream.
    if len(technical) > 6000:
        technical = "…" + technical[-5999:]
    return technical


def _has_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker in text for marker in markers)


def _classification(kind: ErrorKind, technical: str, status: int | None = None):
    return FailureClassification(
        kind=kind,
        retryable=kind in {ErrorKind.TRANSIENT_NETWORK, ErrorKind.RATE_LIMIT},
        user_message=_MESSAGES[kind],
        technical_message=technical,
        http_status=status,
    )


def classify_failure(
    error: BaseException | None = None,
    logger_messages: str | Iterable[str] | None = None,
) -> FailureClassification:
    """Classify a yt-dlp/application failure using structural evidence first.

    This function has no side effects and intentionally does not implement retry
    or auth-refresh policy.
    """
    if isinstance(error, ClassifiedFailureError):
        return error.classification

    embedded = getattr(error, "classification", None)
    if isinstance(embedded, FailureClassification):
        return embedded

    chain = list(_unique_objects(_exception_chain(error)))
    technical = _technical_text(error, logger_messages)
    text = technical.lower()

    # 1) Strong local I/O evidence.  Only filesystem/resource errnos are used;
    # generic OSError is not enough because sockets also derive from OSError.
    for value in chain:
        if isinstance(value, PermissionError):
            return _classification(ErrorKind.LOCAL_IO, technical)
        if isinstance(value, OSError) and getattr(value, "errno", None) in _LOCAL_ERRNOS:
            return _classification(ErrorKind.LOCAL_IO, technical)

    # 2) HTTP status preserved by urllib or yt-dlp networking exceptions.
    status = next((s for s in (_http_status(v) for v in chain) if s is not None), None)
    if status == 429:
        return _classification(ErrorKind.RATE_LIMIT, technical, status)
    if status in _TRANSIENT_HTTP:
        return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)

    # 3) Network exception types / preserved causes.
    for value in chain:
        if isinstance(value, (socket.timeout, TimeoutError, ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)
        if isinstance(value, (http.client.IncompleteRead, http.client.RemoteDisconnected)):
            return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)
        if isinstance(value, urllib.error.URLError) and isinstance(getattr(value, "reason", None), BaseException):
            reason = value.reason
            if isinstance(reason, (socket.timeout, TimeoutError, ConnectionResetError, ConnectionAbortedError)):
                return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)
        if _looks_like_yt_dlp_transport(value):
            # HTTP errors were already handled by status.  Plain RequestError can
            # represent non-network support failures. Certificate verification is
            # also not assumed transient because retrying cannot repair trust/config.
            names = _class_names(value)
            if "CertificateVerifyError" in names or any(marker in text for marker in (
                "certificate verify failed", "certificate_verify_failed", "hostname mismatch",
            )):
                continue
            retryable_names = {
                "TransportError", "IncompleteRead", "SSLError", "ProxyError",
                "ReadTimeout", "ReadTimeoutError", "ConnectTimeout",
                "ConnectTimeoutError", "ProtocolError", "NewConnectionError",
                "RemoteDisconnected",
            }
            if "RequestError" not in names or names & retryable_names:
                return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)

    # 4) HTTP status preserved only in textual diagnostics (common after an
    # outer DownloadError has flattened the original exception).
    text_status = _http_status_from_text(technical)
    if status is None and text_status is not None:
        status = text_status
    if status == 429:
        return _classification(ErrorKind.RATE_LIMIT, technical, status)
    if status in _TRANSIENT_HTTP:
        return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)

    # 5) Text fallback.  Order is deliberate: challenge/EJS evidence must beat
    # the historically ambiguous "page needs to be reloaded" symptom, and
    # explicit private/removed evidence must not be swallowed by a sign-in hint.
    if _has_any(text, _JS_MARKERS):
        return _classification(ErrorKind.JS_RUNTIME, technical, status)

    if _has_any(text, _PERMANENT_MARKERS):
        return _classification(ErrorKind.PERMANENT_UNAVAILABLE, technical, status)

    if _has_any(text, _FORMAT_MARKERS):
        return _classification(ErrorKind.FORMAT_CONFIG, technical, status)

    if _has_any(text, _AUTH_MARKERS):
        return _classification(ErrorKind.AUTH_EXPIRED, technical, status)

    if _has_any(text, _RATE_LIMIT_MARKERS):
        return _classification(ErrorKind.RATE_LIMIT, technical, status)

    if _has_any(text, _NETWORK_MARKERS):
        return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)

    # 401 is unambiguously authentication-related.  A bare 403 remains UNKNOWN:
    # it can mean auth, geo/policy, or a permanently forbidden resource.  Only
    # explicit CDN/signed-media context makes it a bounded re-extraction retry.
    if status == 401:
        return _classification(ErrorKind.AUTH_EXPIRED, technical, status)
    if status == 403 and _has_any(text, _CDN_REEXTRACT_MARKERS):
        return _classification(ErrorKind.TRANSIENT_NETWORK, technical, status)

    return _classification(ErrorKind.UNKNOWN, technical, status)


def technical_summary(classification: FailureClassification, limit: int = 240) -> str:
    """Single-line diagnostic suitable for controlled TUI display."""
    text = " ".join(classification.technical_message.split())
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "…"
    return text

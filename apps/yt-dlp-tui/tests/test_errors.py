import errno
import socket
import urllib.error

import pytest

from yt_dlp_tui.errors import CaptureLogger, ClassifiedFailureError, ErrorKind, classify_failure


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("ERROR: [youtube] x: Sign in to confirm you're not a bot", ErrorKind.AUTH_EXPIRED),
        ("ERROR: cookies are no longer valid", ErrorKind.AUTH_EXPIRED),
        ("ERROR: authentication required", ErrorKind.AUTH_EXPIRED),
        ("HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out.", ErrorKind.TRANSIENT_NETWORK),
        ("ERROR: [youtube] x: video is private", ErrorKind.PERMANENT_UNAVAILABLE),
        ("ERROR: [youtube] x: video has been removed", ErrorKind.PERMANENT_UNAVAILABLE),
        ("ERROR: Requested format is not available", ErrorKind.FORMAT_CONFIG),
        ("something completely new happened", ErrorKind.UNKNOWN),
    ],
)
def test_required_text_classifications(message, expected):
    result = classify_failure(RuntimeError(message))
    assert result.kind is expected


def test_js_challenge_beats_ambiguous_reload_message():
    result = classify_failure(
        RuntimeError("The page needs to be reloaded."),
        ["WARNING: n challenge solving failed: ensure you have a JavaScript runtime and challenge solver"],
    )
    assert result.kind is ErrorKind.JS_RUNTIME
    assert result.kind is not ErrorKind.AUTH_EXPIRED


def test_reload_message_alone_is_not_auth():
    result = classify_failure(RuntimeError("The page needs to be reloaded."))
    assert result.kind is ErrorKind.UNKNOWN


@pytest.mark.parametrize(
    ("status", "expected", "retryable"),
    [
        (503, ErrorKind.TRANSIENT_NETWORK, True),
        (429, ErrorKind.RATE_LIMIT, True),
        (401, ErrorKind.AUTH_EXPIRED, False),
        (403, ErrorKind.UNKNOWN, False),
    ],
)
def test_http_status_classification(status, expected, retryable):
    error = urllib.error.HTTPError("https://example.test", status, "failure", {}, None)
    result = classify_failure(error)
    assert result.kind is expected
    assert result.http_status == status
    assert result.retryable is retryable


def test_permission_error_is_local_io():
    result = classify_failure(PermissionError(errno.EACCES, "Permission denied", "x.part"))
    assert result.kind is ErrorKind.LOCAL_IO
    assert result.retryable is False


def test_disk_full_oserror_is_local_io():
    result = classify_failure(OSError(errno.ENOSPC, "No space left on device"))
    assert result.kind is ErrorKind.LOCAL_IO


def test_timeout_exception_is_transient_network():
    result = classify_failure(socket.timeout("timed out"))
    assert result.kind is ErrorKind.TRANSIENT_NETWORK
    assert result.retryable is True


class WrapperError(RuntimeError):
    def __init__(self, message, cause=None, exc_info=None):
        super().__init__(message)
        self.cause = cause
        self.exc_info = exc_info


def test_preserved_cause_has_priority_over_wrapper_text():
    wrapped = WrapperError(
        "generic download error",
        cause=PermissionError(errno.EACCES, "Permission denied", "file.mp4"),
    )
    result = classify_failure(wrapped)
    assert result.kind is ErrorKind.LOCAL_IO


def test_preserved_exc_info_is_inspected():
    timeout = socket.timeout("read timed out")
    wrapped = WrapperError("generic download error", exc_info=(socket.timeout, timeout, None))
    result = classify_failure(wrapped)
    assert result.kind is ErrorKind.TRANSIENT_NETWORK


class FakeResponse:
    status = 503


class FakeYtDlpHTTPError(RuntimeError):
    def __init__(self):
        super().__init__("HTTP Error 503: Service Unavailable")
        self.response = FakeResponse()


def test_response_status_attribute_is_inspected():
    result = classify_failure(FakeYtDlpHTTPError())
    assert result.kind is ErrorKind.TRANSIENT_NETWORK
    assert result.http_status == 503


def test_private_video_beats_sign_in_hint():
    result = classify_failure(RuntimeError("Private video. Please sign in if you've been granted access"))
    assert result.kind is ErrorKind.PERMANENT_UNAVAILABLE


def test_unknown_retains_diagnostic_message():
    result = classify_failure(RuntimeError("rare frobnicator failure 42"))
    assert result.kind is ErrorKind.UNKNOWN
    assert "rare frobnicator failure 42" in result.technical_message
    assert result.user_message


def test_capture_logger_captures_without_printing(capsys):
    logger = CaptureLogger()
    logger.error("ERROR: very long yt-dlp diagnostic")
    logger.warning("warning")
    assert "very long" in logger.joined()
    assert "warning" in logger.joined()
    assert capsys.readouterr().out == ""


def test_generic_video_unavailable_is_kept_unknown_without_permanent_evidence():
    result = classify_failure(RuntimeError("Video unavailable"))
    assert result.kind is ErrorKind.UNKNOWN


def test_js_evidence_beats_auth_text_even_when_both_are_present():
    result = classify_failure(
        RuntimeError("Sign in to confirm you're not a bot. The page needs to be reloaded."),
        "signature solving failed; EJS challenge solver unavailable",
    )
    assert result.kind is ErrorKind.JS_RUNTIME


class CertificateVerifyError(RuntimeError):
    pass


def test_certificate_verification_is_not_assumed_transient():
    result = classify_failure(CertificateVerifyError("certificate verify failed"))
    assert result.kind is ErrorKind.UNKNOWN


@pytest.mark.parametrize(
    ("message", "expected", "status"),
    [
        ("ERROR: HTTP Error 503: Service Unavailable", ErrorKind.TRANSIENT_NETWORK, 503),
        ("ERROR: HTTP 429 Too Many Requests", ErrorKind.RATE_LIMIT, 429),
        ("ERROR: HTTP Error 403: Forbidden", ErrorKind.UNKNOWN, 403),
    ],
)
def test_http_status_can_be_recovered_from_flattened_text(message, expected, status):
    result = classify_failure(RuntimeError(message))
    assert result.kind is expected
    assert result.http_status == status


def test_already_classified_failure_preserves_logger_context_across_layers():
    original = classify_failure(
        RuntimeError("The page needs to be reloaded."),
        "n challenge solving failed; JavaScript runtime required",
    )
    carried = ClassifiedFailureError(original)
    again = classify_failure(carried)
    assert again is original
    assert again.kind is ErrorKind.JS_RUNTIME
    assert "n challenge solving failed" in again.technical_message

class ReadTimeoutError(RuntimeError):
    pass


class ConnectTimeoutError(RuntimeError):
    pass


@pytest.mark.parametrize('error_type', [ReadTimeoutError, ConnectTimeoutError])
def test_external_timeout_class_names_are_transient(error_type):
    result = classify_failure(error_type('connection timed out'))
    assert result.kind is ErrorKind.TRANSIENT_NETWORK
    assert result.retryable is True


@pytest.mark.parametrize('status', [408, 425, 500, 502, 503, 504])
def test_all_required_transient_http_statuses(status):
    error = urllib.error.HTTPError('https://example.test', status, 'temporary', {}, None)
    result = classify_failure(error)
    assert result.kind is ErrorKind.TRANSIENT_NETWORK
    assert result.http_status == status


def test_rate_limit_text_without_status_is_rate_limit():
    result = classify_failure(RuntimeError('Too Many Requests: rate limited by upstream'))
    assert result.kind is ErrorKind.RATE_LIMIT


def test_bare_403_stays_unknown_but_googlevideo_403_is_bounded_transient():
    bare = classify_failure(RuntimeError('HTTP Error 403: Forbidden'))
    cdn = classify_failure(RuntimeError('HTTP Error 403: Forbidden from rr3---sn-x.googlevideo.com signed URL'))
    assert bare.kind is ErrorKind.UNKNOWN
    assert cdn.kind is ErrorKind.TRANSIENT_NETWORK


def test_403_with_auth_evidence_is_auth_not_network():
    result = classify_failure(RuntimeError("HTTP Error 403: Sign in to confirm you're not a bot"))
    assert result.kind is ErrorKind.AUTH_EXPIRED


def test_403_with_js_challenge_evidence_is_js_runtime():
    result = classify_failure(
        RuntimeError('HTTP Error 403: Forbidden from googlevideo.com'),
        ['signature solving failed; JavaScript challenge solver unavailable'],
    )
    assert result.kind is ErrorKind.JS_RUNTIME


@pytest.mark.parametrize('message', [
    '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol',
    'TLSV1 alert internal error',
])
def test_temporary_ssl_transport_messages_are_transient(message):
    assert classify_failure(RuntimeError(message)).kind is ErrorKind.TRANSIENT_NETWORK

class SSLError(RuntimeError):
    pass


def test_ssl_certificate_failure_is_not_transient_even_if_sslerror_class():
    result = classify_failure(SSLError('[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed'))
    assert result.kind is ErrorKind.UNKNOWN

@pytest.mark.parametrize("message", [
    "This video is available to members of this channel only",
    "This video is age restricted",
    "The uploader has not made this video available in your country",
])
def test_restrictions_are_not_forced_to_permanent_unavailable(message):
    result = classify_failure(RuntimeError(message))
    assert result.kind is not ErrorKind.PERMANENT_UNAVAILABLE

@pytest.mark.parametrize("message", [
    "This video is no longer available",
    "This video has been deleted",
])
def test_inequivocal_no_longer_available_is_permanent(message):
    result = classify_failure(RuntimeError(message))
    assert result.kind is ErrorKind.PERMANENT_UNAVAILABLE

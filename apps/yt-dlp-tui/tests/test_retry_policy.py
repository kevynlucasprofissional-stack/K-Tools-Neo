from yt_dlp_tui.errors import ErrorKind, FailureClassification
from yt_dlp_tui.retry_policy import (
    MAX_EXTERNAL_ATTEMPTS,
    RATE_LIMIT_BACKOFF_SECONDS,
    TRANSIENT_BACKOFF_SECONDS,
    YT_DLP_EXTRACTOR_RETRIES,
    YT_DLP_FILE_ACCESS_RETRIES,
    YT_DLP_FRAGMENT_RETRIES,
    YT_DLP_RETRIES,
    YT_DLP_SOCKET_TIMEOUT,
    exhausted_message,
    is_network_retryable,
    retry_decision,
    worst_case_explicit_wait_seconds,
    yt_dlp_retry_options,
)


def failure(kind):
    return FailureClassification(kind, kind in {ErrorKind.TRANSIENT_NETWORK, ErrorKind.RATE_LIMIT}, 'u', 't')


def test_internal_yt_dlp_budget_is_explicit_and_small():
    opts = yt_dlp_retry_options()
    assert opts['retries'] == YT_DLP_RETRIES == 1
    assert opts['fragment_retries'] == YT_DLP_FRAGMENT_RETRIES == 2
    assert opts['extractor_retries'] == YT_DLP_EXTRACTOR_RETRIES == 1
    assert opts['file_access_retries'] == YT_DLP_FILE_ACCESS_RETRIES == 1
    assert opts['socket_timeout'] == YT_DLP_SOCKET_TIMEOUT == 15.0
    assert set(opts['retry_sleep_functions']) == {'http', 'fragment', 'extractor', 'file_access'}
    assert all(callable(fn) for fn in opts['retry_sleep_functions'].values())


def test_transient_network_has_only_two_external_retries():
    f = failure(ErrorKind.TRANSIENT_NETWORK)
    first = retry_decision(f, 1)
    second = retry_decision(f, 2)
    third = retry_decision(f, 3)
    assert MAX_EXTERNAL_ATTEMPTS == 3
    assert (first.retry, first.delay_seconds) == (True, TRANSIENT_BACKOFF_SECONDS[0])
    assert (second.retry, second.delay_seconds) == (True, TRANSIENT_BACKOFF_SECONDS[1])
    assert third.retry is False


def test_rate_limit_uses_larger_backoff():
    f = failure(ErrorKind.RATE_LIMIT)
    assert retry_decision(f, 1).delay_seconds == RATE_LIMIT_BACKOFF_SECONDS[0]
    assert retry_decision(f, 2).delay_seconds == RATE_LIMIT_BACKOFF_SECONDS[1]
    assert retry_decision(f, 1).delay_seconds > retry_decision(failure(ErrorKind.TRANSIENT_NETWORK), 1).delay_seconds


def test_non_network_categories_never_enter_network_retry():
    for kind in (
        ErrorKind.AUTH_EXPIRED,
        ErrorKind.PERMANENT_UNAVAILABLE,
        ErrorKind.JS_RUNTIME,
        ErrorKind.LOCAL_IO,
        ErrorKind.FORMAT_CONFIG,
        ErrorKind.UNKNOWN,
    ):
        f = failure(kind)
        assert is_network_retryable(f) is False
        assert retry_decision(f, 1).retry is False


def test_explicit_outer_wait_is_bounded():
    assert worst_case_explicit_wait_seconds(ErrorKind.TRANSIENT_NETWORK) == 9.0
    assert worst_case_explicit_wait_seconds(ErrorKind.RATE_LIMIT) == 30.0
    assert worst_case_explicit_wait_seconds(ErrorKind.AUTH_EXPIRED) == 0.0
    assert '3 tentativas' in exhausted_message(failure(ErrorKind.TRANSIENT_NETWORK))


def test_internal_retry_sleep_accepts_yt_dlp_n_keyword():
    from yt_dlp_tui.retry_policy import _internal_sleep
    assert _internal_sleep(n=0) == 0.5
    assert _internal_sleep(n=1) == 1.0
    assert _internal_sleep(n=2) == 2.0
    assert _internal_sleep(n=99) == 2.0


def test_internal_retry_sleep_tolerates_future_extra_keywords():
    from yt_dlp_tui.retry_policy import _internal_sleep
    assert _internal_sleep(n=1, error="timeout") == 1.0

"""Bounded retry policy for transient YouTube/network failures.

The central classifier decides *what* failed.  This module decides whether a
classified transient failure may be retried and how long to wait.  It also
reduces yt-dlp's internal retry defaults so the application-level restart loop
cannot multiply into dozens of attempts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ErrorKind, FailureClassification


# yt-dlp defaults are currently much larger (download 10, fragments 10,
# extractor 3, file access 3).  We intentionally keep the internal budget low
# because YT-DLP TUI can restart/re-extract an entire item up to three times.
YT_DLP_RETRIES = 1
YT_DLP_FRAGMENT_RETRIES = 2
YT_DLP_EXTRACTOR_RETRIES = 1
YT_DLP_FILE_ACCESS_RETRIES = 1
YT_DLP_SOCKET_TIMEOUT = 15.0

# One initial application attempt + at most two complete restarts/re-extractions.
MAX_EXTERNAL_ATTEMPTS = 3

TRANSIENT_BACKOFF_SECONDS = (3.0, 6.0)
RATE_LIMIT_BACKOFF_SECONDS = (10.0, 20.0)


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    attempt: int
    max_attempts: int
    delay_seconds: float
    kind: ErrorKind


def _internal_sleep(n=0, **_kwargs) -> float:
    """Small bounded delay compatible with yt-dlp's retry callback contract.

    Current yt-dlp invokes retry sleep callbacks with the retry number as the
    keyword argument ``n``.  Accept extra keyword arguments defensively so a
    harmless callback API extension cannot abort a media download.
    """
    try:
        retry_number = max(0, int(n))
    except (TypeError, ValueError):
        retry_number = 0
    return min(0.5 * (2 ** retry_number), 2.0)


def yt_dlp_retry_options() -> dict:
    """Explicit yt-dlp retry parameters used by all network operations."""
    return {
        "retries": YT_DLP_RETRIES,
        "fragment_retries": YT_DLP_FRAGMENT_RETRIES,
        "extractor_retries": YT_DLP_EXTRACTOR_RETRIES,
        "file_access_retries": YT_DLP_FILE_ACCESS_RETRIES,
        "socket_timeout": YT_DLP_SOCKET_TIMEOUT,
        "retry_sleep_functions": {
            "http": _internal_sleep,
            "fragment": _internal_sleep,
            "extractor": _internal_sleep,
            "file_access": _internal_sleep,
        },
    }


def is_network_retryable(failure: FailureClassification) -> bool:
    """Only central-classifier network/rate-limit categories are retryable here."""
    return failure.kind in {ErrorKind.TRANSIENT_NETWORK, ErrorKind.RATE_LIMIT}


def retry_decision(failure: FailureClassification, attempt: int) -> RetryDecision:
    """Return the decision after a failed application-level attempt.

    ``attempt`` is 1-based and is the attempt that just failed.  With
    MAX_EXTERNAL_ATTEMPTS=3, failures after attempts 1 and 2 may retry; failure
    after attempt 3 is exhausted.
    """
    if not is_network_retryable(failure) or attempt >= MAX_EXTERNAL_ATTEMPTS:
        return RetryDecision(False, attempt, MAX_EXTERNAL_ATTEMPTS, 0.0, failure.kind)

    delays = RATE_LIMIT_BACKOFF_SECONDS if failure.kind is ErrorKind.RATE_LIMIT else TRANSIENT_BACKOFF_SECONDS
    delay_index = min(max(attempt - 1, 0), len(delays) - 1)
    return RetryDecision(True, attempt, MAX_EXTERNAL_ATTEMPTS, delays[delay_index], failure.kind)


def exhausted_message(failure: FailureClassification) -> str:
    if failure.kind is ErrorKind.RATE_LIMIT:
        return f"O YouTube continuou limitando as requisições após {MAX_EXTERNAL_ATTEMPTS} tentativas."
    return f"A conexão com o YouTube continuou instável após {MAX_EXTERNAL_ATTEMPTS} tentativas."


def worst_case_explicit_wait_seconds(kind: ErrorKind) -> float:
    """Wait introduced by the outer policy, excluding network socket time itself."""
    if kind is ErrorKind.RATE_LIMIT:
        return sum(RATE_LIMIT_BACKOFF_SECONDS[: MAX_EXTERNAL_ATTEMPTS - 1])
    if kind is ErrorKind.TRANSIENT_NETWORK:
        return sum(TRANSIENT_BACKOFF_SECONDS[: MAX_EXTERNAL_ATTEMPTS - 1])
    return 0.0

from __future__ import annotations


class RetryPolicy:
    """
    When to retry: on 429, 503 and a failed connection, at most max_retries times, waiting what Retry-After asks (or 1, 2,
    4 seconds without it). A wait longer than max_wait_seconds is not slept through: the error goes to the caller with
    retry_after_seconds, so a request never hangs for minutes during maintenance.
    """

    def __init__(self, max_retries: int = 2, max_wait_seconds: int = 10) -> None:
        if max_retries < 0 or max_wait_seconds < 0:
            raise ValueError("max_retries and max_wait_seconds must not be negative")
        self.max_retries = max_retries
        self.max_wait_seconds = max_wait_seconds

    @classmethod
    def none(cls) -> RetryPolicy:
        return cls(0, 0)

    def wait_before(self, attempt: int, retry_after_seconds: int | None) -> int | None:
        """Seconds to wait before the next attempt, or None when the call must not be retried. ``attempt`` counts from 1."""
        if attempt > self.max_retries:
            return None
        wait = retry_after_seconds if retry_after_seconds is not None else 1 << (attempt - 1)
        return wait if wait <= self.max_wait_seconds else None

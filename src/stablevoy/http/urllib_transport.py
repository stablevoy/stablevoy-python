from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from urllib.parse import urlencode, urlsplit
from urllib.request import Request

from stablevoy.errors.api_error import ApiError
from stablevoy.errors.configuration_error import ConfigurationError
from stablevoy.errors.transport_error import TransportError
from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.http.error_factory import ErrorFactory
from stablevoy.http.http_answer import HttpAnswer
from stablevoy.http.opener import Opener
from stablevoy.http.retry_policy import RetryPolicy

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class UrllibTransport:
    """
    The API over HTTP: Bearer API key, JSON in and out, errors as exceptions, and retries only where a repeat cannot do
    harm (reads, and creates that carry an Idempotency-Key).
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        user_agent: str,
        retries: RetryPolicy,
        opener: Opener,
        sleep: Callable[[float], None],
        errors: ErrorFactory,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ConfigurationError("The API key is empty. Create one in the Stablevoy dashboard.")
        if not 0 < timeout_seconds <= 600:
            raise ConfigurationError(f"timeout_seconds must be more than 0 and at most 600; got {timeout_seconds}")
        self._api_key = api_key
        self._base_url = self._checked_base_url(base_url)
        self._user_agent = user_agent
        self._retries = retries
        self._opener = opener
        self._sleep = sleep
        self._errors = errors
        self._timeout = timeout_seconds

    def get(self, path: str, query: Mapping[str, str | int] | None = None) -> object:
        url = self._base_url + path + (f"?{urlencode(query)}" if query else "")
        return self._send(Request(url, method="GET"), retryable=True)  # noqa: S310 - the scheme is checked to be http(s)

    def post(self, path: str, body: Mapping[str, object], idempotency_key: str | None = None) -> object:
        request = Request(self._base_url + path, data=json.dumps(body).encode(), method="POST")  # noqa: S310 - checked scheme
        request.add_header("Content-Type", "application/json")
        if idempotency_key is not None:
            request.add_header("Idempotency-Key", idempotency_key)
        return self._send(request, retryable=idempotency_key is not None)

    def _send(self, request: Request, *, retryable: bool) -> object:
        request.add_header("Authorization", f"Bearer {self._api_key}")
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", self._user_agent)
        attempt = 1
        while True:
            try:
                answer = self._opener.send(request, self._timeout)
            except OSError as error:
                wait = self._retries.wait_before(attempt, None) if retryable else None
                if wait is None:
                    raise TransportError(f"Cannot reach the Stablevoy API: {error}") from error
                self._sleep(wait)
                attempt += 1
                continue
            if 200 <= answer.status < 300:
                return self._decode(answer.body)
            api_error = self._errors.from_problem(answer.status, answer.body, self._retry_after(answer))
            retry = retryable and self._is_retryable(api_error)
            wait = self._retries.wait_before(attempt, api_error.retry_after_seconds) if retry else None
            if wait is None:
                raise api_error
            self._sleep(wait)
            attempt += 1

    @staticmethod
    def _is_retryable(error: ApiError) -> bool:
        return error.status in (429, 503)

    @staticmethod
    def _decode(body: bytes) -> object:
        try:
            value: object = json.loads(body)
        except ValueError as error:
            raise UnexpectedResponseError("The API answered with a body that is not JSON") from error
        if not isinstance(value, dict | list):
            raise UnexpectedResponseError("The API answered with JSON that is not an object or a list")
        return value

    @staticmethod
    def _retry_after(answer: HttpAnswer) -> int | None:
        value = (answer.headers.get("Retry-After") or "").strip()
        return int(value) if re.fullmatch(r"\d{1,9}", value) else None

    @staticmethod
    def _checked_base_url(base_url: str) -> str:
        """
        Only a scheme, a host and an optional port. The API key travels in every request, so plain http is refused except
        for a local development server, and so are credentials, paths, queries and fragments in the URL.
        """
        url = base_url.rstrip("/")
        try:
            parts = urlsplit(url)
            _ = parts.port  # raises ValueError on a port that is no number
        except ValueError:
            parts = None
        bad = (
            parts is None
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or bool(parts.path or parts.query or parts.fragment)
            or not (parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in _LOCAL_HOSTS))
        )
        if bad:
            raise ConfigurationError(
                f"The base URL must be https and only a host, like https://api.stablevoy.com (http only for localhost); got {base_url}"
            )
        return url

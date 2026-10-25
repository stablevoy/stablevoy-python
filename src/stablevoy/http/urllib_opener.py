from __future__ import annotations

from urllib.error import HTTPError
from urllib.request import OpenerDirector, Request, build_opener

from stablevoy.http.http_answer import HttpAnswer
from stablevoy.http.no_redirects import NoRedirects


class UrllibOpener:
    """The standard library's HTTP client without redirects. Error statuses come back as answers, not exceptions."""

    def __init__(self, opener: OpenerDirector | None = None) -> None:
        self._opener = opener if opener is not None else build_opener(NoRedirects)

    def send(self, request: Request, timeout: float) -> HttpAnswer:
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return HttpAnswer(response.status, response.headers, response.read())
        except HTTPError as error:
            with error:
                return HttpAnswer(error.code, error.headers, error.read())

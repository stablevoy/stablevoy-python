from __future__ import annotations

from collections.abc import Callable
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.request import OpenerDirector, Request, build_opener

from stablevoy.http.deadline import Deadline
from stablevoy.http.deadline_http_handler import DeadlineHTTPHandler
from stablevoy.http.deadline_https_handler import DeadlineHTTPSHandler
from stablevoy.http.http_answer import HttpAnswer
from stablevoy.http.no_redirects import NoRedirects


def _default_opener(deadline: Deadline) -> OpenerDirector:
    return build_opener(NoRedirects, DeadlineHTTPHandler(deadline), DeadlineHTTPSHandler(deadline))


class UrllibOpener:
    """
    The standard library's HTTP client without redirects, each exchange bounded as a whole by the timeout. Error
    statuses come back as answers; a missing, cut or broken answer is an OSError.
    """

    def __init__(self, opener_for: Callable[[Deadline], OpenerDirector] = _default_opener) -> None:
        self._opener_for = opener_for

    def send(self, request: Request, timeout: float) -> HttpAnswer:
        deadline = Deadline(timeout)
        try:
            with self._opener_for(deadline).open(request, timeout=timeout) as response:
                return HttpAnswer(response.status, response.headers, response.read())
        except HTTPError as error:
            with error:
                return HttpAnswer(error.code, error.headers, error.read())
        except (OSError, HTTPException) as error:
            if deadline.expired:
                raise TimeoutError(f"no complete answer within {timeout:g} s") from error
            if isinstance(error, HTTPException):
                raise ConnectionError(f"broken answer: {error!r}") from error
            raise
        finally:
            deadline.cancel()

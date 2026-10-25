from __future__ import annotations

from functools import partial
from http.client import HTTPResponse
from urllib.request import HTTPHandler, Request

from stablevoy.http.deadline import Deadline
from stablevoy.http.deadline_http_connection import DeadlineHTTPConnection


class DeadlineHTTPHandler(HTTPHandler):
    """Opens http:// requests over a DeadlineHTTPConnection."""

    def __init__(self, deadline: Deadline) -> None:
        super().__init__()
        self._deadline = deadline

    def http_open(self, req: Request) -> HTTPResponse:
        return self.do_open(partial(DeadlineHTTPConnection, deadline=self._deadline), req)

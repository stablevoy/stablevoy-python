from __future__ import annotations

import ssl
from functools import partial
from http.client import HTTPResponse
from urllib.request import HTTPSHandler, Request

from stablevoy.http.deadline import Deadline
from stablevoy.http.deadline_https_connection import DeadlineHTTPSConnection


class DeadlineHTTPSHandler(HTTPSHandler):
    """Opens https:// requests over a DeadlineHTTPSConnection; `context` None means the default verified context."""

    def __init__(self, deadline: Deadline, context: ssl.SSLContext | None = None) -> None:
        super().__init__(context=context)
        self._deadline = deadline
        self._tls = context

    def https_open(self, req: Request) -> HTTPResponse:
        return self.do_open(partial(DeadlineHTTPSConnection, deadline=self._deadline), req, context=self._tls)

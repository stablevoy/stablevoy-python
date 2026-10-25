from __future__ import annotations

import ssl
from http.client import HTTPSConnection

from stablevoy.http.deadline import Deadline


class DeadlineHTTPSConnection(HTTPSConnection):
    """HTTPS under a Deadline; certificate checks stay the standard library's defaults."""

    def __init__(self, host: str, *, timeout: float, context: ssl.SSLContext | None, deadline: Deadline) -> None:
        super().__init__(host, timeout=timeout, context=context)
        self._deadline = deadline

    def connect(self) -> None:
        super().connect()
        self._deadline.watch(self.sock)

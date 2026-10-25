from __future__ import annotations

from http.client import HTTPConnection

from stablevoy.http.deadline import Deadline


class DeadlineHTTPConnection(HTTPConnection):
    """Plain HTTP (a local development server only) under a Deadline."""

    def __init__(self, host: str, *, timeout: float, deadline: Deadline) -> None:
        super().__init__(host, timeout=timeout)
        self._deadline = deadline

    def connect(self) -> None:
        super().connect()
        self._deadline.watch(self.sock)

from __future__ import annotations

import contextlib
import socket
import threading
import time


class Deadline:
    """
    Bounds the whole exchange, not only silence. The socket timeout fires when nothing arrives for that long, so a
    server sending one byte at a time could keep a request open forever; when the time is up this shuts the socket down,
    which ends any read in progress.
    """

    def __init__(self, seconds: float) -> None:
        self._ends_at = time.monotonic() + seconds
        self._timer: threading.Timer | None = None
        self.expired = False

    def watch(self, sock: socket.socket) -> None:
        timer = threading.Timer(max(0.0, self._ends_at - time.monotonic()), self._expire, (sock,))
        timer.daemon = True
        self._timer = timer
        timer.start()

    def cancel(self) -> None:
        if self._timer is not None:
            self._timer.cancel()

    def _expire(self, sock: socket.socket) -> None:
        self.expired = True
        # OSError: the connection was already closed, nothing left to stop.
        with contextlib.suppress(OSError):
            sock.shutdown(socket.SHUT_RDWR)

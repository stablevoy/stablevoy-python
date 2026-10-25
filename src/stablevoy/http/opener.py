from typing import Protocol
from urllib.request import Request

from stablevoy.http.http_answer import HttpAnswer


class Opener(Protocol):
    """Sends a request and returns the answer, whatever its status; raises OSError when there is no answer at all."""

    def send(self, request: Request, timeout: float) -> HttpAnswer: ...

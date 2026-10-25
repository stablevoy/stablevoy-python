from __future__ import annotations

from email.message import Message
from typing import IO
from urllib.request import HTTPRedirectHandler, Request


class NoRedirects(HTTPRedirectHandler):
    """The API never redirects; following one would carry the key wherever it points. The 3xx answer is returned as is."""

    def redirect_request(self, req: Request, fp: IO[bytes], code: int, msg: str, headers: Message, newurl: str) -> None:  # noqa: PLR0917 - urllib defines this signature
        return None

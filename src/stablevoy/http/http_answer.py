from dataclasses import dataclass
from email.message import Message


@dataclass(frozen=True)
class HttpAnswer:
    status: int
    headers: Message
    body: bytes

from __future__ import annotations

import json
from dataclasses import dataclass, field
from email.message import Message
from pathlib import Path
from urllib.request import Request

from stablevoy import RetryPolicy, Stablevoy
from stablevoy.http.http_answer import HttpAnswer

FIXTURES = Path(__file__).parent / "fixtures"
OPENAPI: dict[str, object] = json.loads((FIXTURES / "openapi.json").read_text())
INVOICE_ID = "7c3360b5-e8cc-4775-8a13-7324d4f1296e"


def example_value(method: str, path: str, status: int) -> object:
    """A response example of the API's own OpenAPI document (tests/fixtures/openapi.json), object or list."""
    node: object = OPENAPI
    for key in ("paths", path, method.lower(), "responses", str(status), "content", "application/json", "example"):
        assert isinstance(node, dict), f"no example for {method} {path} {status} at {key}"
        node = node[key]
    return node


def example(method: str, path: str, status: int) -> dict[str, object]:
    """A response example that is a JSON object."""
    node = example_value(method, path, status)
    assert isinstance(node, dict)
    return node


def answer(status: int, body: object, headers: dict[str, str] | None = None) -> HttpAnswer:
    message = Message()
    message["Content-Type"] = "application/problem+json" if status >= 400 else "application/json"
    for key, value in (headers or {}).items():
        message[key] = value
    return HttpAnswer(status, message, body.encode() if isinstance(body, str) else json.dumps(body).encode())


def problem(status: int, code: str, detail: str) -> dict[str, object]:
    return {"type": f"https://stablevoy.com/docs/api/errors/#error-{code}", "title": code, "status": status, "code": code, "detail": detail}


@dataclass
class Sent:
    url: str
    method: str
    headers: dict[str, str]
    body: bytes | None
    timeout: float


@dataclass
class FakeOpener:
    """Answers from a queue (an answer or an OSError per call) and records every request."""

    answers: list[HttpAnswer | OSError]
    sent: list[Sent] = field(default_factory=list)

    def send(self, request: Request, timeout: float) -> HttpAnswer:
        data = request.data if isinstance(request.data, bytes) else None
        self.sent.append(Sent(request.full_url, request.get_method(), dict(request.header_items()), data, timeout))
        if not self.answers:
            raise AssertionError("FakeOpener got more requests than answers")
        next_answer = self.answers.pop(0)
        if isinstance(next_answer, OSError):
            raise next_answer
        return next_answer

    @property
    def last(self) -> Sent:
        return self.sent[-1]


@dataclass
class TestClient:
    client: Stablevoy
    opener: FakeOpener
    slept: list[float]


def client(*answers: HttpAnswer | OSError, retries: RetryPolicy | None = None, base_url: str = "https://api.stablevoy.com") -> TestClient:
    opener = FakeOpener(list(answers))
    slept: list[float] = []
    built = Stablevoy.create("sk_test_key", base_url=base_url, retries=retries, opener=opener, sleep=slept.append)
    return TestClient(built, opener, slept)

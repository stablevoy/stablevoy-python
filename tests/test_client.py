from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import stablevoy
from stablevoy import ApiError, ConfigurationError, RetryPolicy, Stablevoy, TransportError

from .support import answer, client

LIMITS = {"minInvoiceUsdCents": 500, "maxInvoiceUsdCents": 100000}


def test_talks_to_the_configured_host_and_names_the_integration() -> None:
    t = client(answer(200, LIMITS), base_url="http://localhost:8080/")
    t.client.platform.limits()
    assert t.opener.last.url == "http://localhost:8080/v1/limits"


@pytest.mark.parametrize(
    "base_url",
    [
        "http://api.stablevoy.com",
        "https://user:secret@api.stablevoy.com",
        "https://api.stablevoy.com/v1",
        "https://api.stablevoy.com?x=1",
        "https://api.stablevoy.com#x",
        "api.stablevoy.com",
        "ftp://api.stablevoy.com",
        "https://",
        "https://api.stablevoy.com:port",
    ],
)
def test_refuses_a_base_url_that_could_leak_the_key_or_misroute(base_url: str) -> None:
    with pytest.raises(ConfigurationError, match="must be https"):
        Stablevoy.create("sk_test_key", base_url=base_url)


@pytest.mark.parametrize(
    "base_url", ["https://api.stablevoy.com:8443", "http://localhost:8080", "http://127.0.0.1:18700", "http://[::1]:8080"]
)
def test_allows_https_with_a_port_and_plain_http_only_for_local_development(base_url: str) -> None:
    t = client(answer(200, LIMITS), base_url=base_url)
    t.client.platform.limits()
    assert t.opener.last.url == f"{base_url}/v1/limits"


def test_refuses_an_empty_key() -> None:
    with pytest.raises(ConfigurationError, match="API key is empty"):
        Stablevoy.create("  ")


def test_names_the_integration_in_the_user_agent() -> None:
    t = client(answer(200, LIMITS))
    built = Stablevoy.create("sk_test_key", opener=t.opener, user_agent_suffix="my-shop/2.1")
    built.platform.limits()
    assert t.opener.last.headers["User-agent"].endswith(" my-shop/2.1")


def test_exports_the_version() -> None:
    assert stablevoy.__version__ == "1.0.0"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/v1/limits":
            self._reply(200, b'{"minInvoiceUsdCents":500,"maxInvoiceUsdCents":100000}')
        elif self.path == "/v1/store":
            self.send_response(302)
            self.send_header("Location", "https://evil.example/steal")
            self.end_headers()
        else:
            self._reply(404, b'{"code":"not_found","detail":"No such endpoint"}')

    def _reply(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def local_api() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_talks_over_real_http_with_the_standard_library(local_api: str) -> None:
    built = Stablevoy.create("sk_test_key", base_url=local_api)
    assert built.platform.limits().min_invoice_usd_cents == 500
    with pytest.raises(ApiError, match="No such endpoint"):
        built.platform.pricing()


def test_never_follows_a_redirect_with_the_key(local_api: str) -> None:
    built = Stablevoy.create("sk_test_key", base_url=local_api, retries=RetryPolicy.none())
    with pytest.raises(ApiError) as caught:
        built.stores.current()
    assert caught.value.status == 302


def test_reports_a_server_that_does_not_answer() -> None:
    built = Stablevoy.create("sk_test_key", base_url="http://127.0.0.1:9", retries=RetryPolicy.none(), timeout_seconds=2)
    with pytest.raises(TransportError):
        built.platform.limits()

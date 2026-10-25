from __future__ import annotations

import math
import socket
import ssl
import subprocess
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import build_opener

import pytest

import stablevoy
from stablevoy import ApiError, ConfigurationError, RetryPolicy, Stablevoy, TransportError
from stablevoy.http.deadline import Deadline
from stablevoy.http.deadline_http_handler import DeadlineHTTPHandler
from stablevoy.http.deadline_https_handler import DeadlineHTTPSHandler
from stablevoy.http.no_redirects import NoRedirects
from stablevoy.http.urllib_opener import UrllibOpener

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
    assert stablevoy.__version__ == "1.0.1"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/v1/limits":
            self._reply(200, b'{"minInvoiceUsdCents":500,"maxInvoiceUsdCents":100000}')
        elif self.path == "/v1/store":
            self.send_response(302)
            self.send_header("Location", "https://evil.example/steal")
            self.end_headers()
        elif self.path == "/v1/networks":
            self._drip()
        elif self.path.startswith("/v1/invoices"):
            self.send_response(200)
            self.send_header("Content-Length", "1000")
            self.end_headers()
            self.wfile.write(b'{"items":')
        else:
            self._reply(404, b'{"code":"not_found","detail":"No such endpoint"}')

    def _drip(self) -> None:
        """Headers, then one byte at a time: never silent long enough for a socket timeout."""
        self.send_response(200)
        self.send_header("Content-Length", "1000")
        self.end_headers()
        try:
            for _ in range(150):
                self.wfile.write(b" ")
                self.wfile.flush()
                time.sleep(0.02)
        except OSError:
            pass  # the client gave up, which is what the test expects

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


def test_cuts_off_a_server_that_answers_one_byte_at_a_time(local_api: str) -> None:
    built = Stablevoy.create("sk_test_key", base_url=local_api, retries=RetryPolicy.none(), timeout_seconds=0.3)
    started = time.monotonic()
    with pytest.raises(TransportError, match=r"no complete answer within 0\.3 s"):
        built.platform.networks()
    assert time.monotonic() - started < 2


def test_reports_an_answer_cut_short_as_a_transport_error(local_api: str) -> None:
    built = Stablevoy.create("sk_test_key", base_url=local_api, retries=RetryPolicy.none())
    with pytest.raises(TransportError, match="broken answer"):
        built.invoices.list()


@pytest.mark.parametrize("timeout_seconds", [0, -1, math.nan, 601])
def test_refuses_a_timeout_out_of_range(timeout_seconds: float) -> None:
    with pytest.raises(ConfigurationError, match="timeout_seconds must be more than 0 and at most 600"):
        Stablevoy.create("sk_test_key", timeout_seconds=timeout_seconds)


def test_a_deadline_on_a_closed_socket_only_marks_itself_expired() -> None:
    deadline = Deadline(0)
    sock = socket.socket()
    sock.close()
    deadline._expire(sock)
    assert deadline.expired


@pytest.fixture
def local_tls_api(tmp_path: Path) -> Iterator[tuple[str, ssl.SSLContext]]:
    key, cert = tmp_path / "key.pem", tmp_path / "cert.pem"
    subprocess.run(  # noqa: S603 - fixed arguments, test certificate only
        [  # noqa: S607 - the system openssl, test certificate only
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "ec",
            "-pkeyopt",
            "ec_paramgen_curve:P-256",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        capture_output=True,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    served = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    served.load_cert_chain(cert, key)
    server.socket = served.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    trusted = ssl.create_default_context(cafile=str(cert))
    yield f"https://localhost:{server.server_address[1]}", trusted
    server.shutdown()
    server.server_close()


def test_bounds_https_exchanges_too(local_tls_api: tuple[str, ssl.SSLContext]) -> None:
    url, trusted = local_tls_api
    opener = UrllibOpener(lambda d: build_opener(NoRedirects, DeadlineHTTPHandler(d), DeadlineHTTPSHandler(d, trusted)))
    built = Stablevoy.create("sk_test_key", base_url=url, opener=opener, retries=RetryPolicy.none(), timeout_seconds=0.3)
    assert built.platform.limits().min_invoice_usd_cents == 500
    with pytest.raises(TransportError, match="no complete answer"):
        built.platform.networks()

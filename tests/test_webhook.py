from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass

import pytest

from stablevoy import SignatureError, WebhookVerifier

from .support import FIXTURES

VECTORS = json.loads((FIXTURES / "webhook-vectors.json").read_text())
SECRET: str = VECTORS["secret"]
PAID, TEST = VECTORS["cases"]


@dataclass
class At:
    now_seconds: int

    def now(self) -> int:
        return self.now_seconds


def test_accepts_what_the_api_signed_as_text_or_bytes() -> None:
    for case in VECTORS["cases"]:
        verifier = WebhookVerifier(SECRET, clock=At(case["timestamp"] + 10))
        body = json.loads(case["body"])
        assert verifier.verify(case["body"], case["header"]).id == body["id"]
        assert verifier.verify(case["body"].encode(), case["header"]).type == body["type"]


def test_gives_the_invoice_of_an_invoice_event_and_the_data_of_others() -> None:
    event = WebhookVerifier(SECRET, clock=At(PAID["timestamp"])).verify(PAID["body"], PAID["header"])
    assert event.invoice is not None
    assert event.created_at.isoformat() == "2026-10-25T10:00:00+00:00"
    other = WebhookVerifier(SECRET, clock=At(TEST["timestamp"])).verify(TEST["body"], TEST["header"])
    assert other.invoice is None
    assert other.data["message"] == "Test event from Stablevoy, café"


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"body": PAID["body"].replace("paid", "pa1d")}, "does not match"),
        ({"secret": "whsec_other"}, "does not match"),
        ({"header": None}, "header is missing"),
        ({"header": "  "}, "header is missing"),
        ({"header": "v1=abc"}, "malformed"),
        ({"header": f"t={PAID['timestamp']}"}, "malformed"),
        ({"header": f"t=99999999999999999999,v1={'a' * 64}"}, "malformed"),
        ({"header": f"t={PAID['timestamp']},v1=NOT-HEX"}, "malformed"),
        ({"now": PAID["timestamp"] + 301}, "too old"),
        ({"now": PAID["timestamp"] - 301}, "too old"),
    ],
)
def test_refuses_what_stablevoy_did_not_sign(change: dict[str, object], reason: str) -> None:
    case = {"body": PAID["body"], "header": PAID["header"], "secret": SECRET, "now": PAID["timestamp"], **change}
    with pytest.raises(SignatureError, match=reason):
        WebhookVerifier(str(case["secret"]), clock=At(int(str(case["now"])))).verify(str(case["body"]), case["header"])


def test_accepts_any_of_several_signatures() -> None:
    header = PAID["header"].replace(",v1=", f",v1={'0' * 64},v1=")
    assert WebhookVerifier(SECRET, clock=At(PAID["timestamp"])).verify(PAID["body"], header).type == "invoice.paid"


@pytest.mark.parametrize(("body", "reason"), [("hello", "is not JSON"), ('{"hello":"world"}', "is not a Stablevoy event")])
def test_refuses_a_signed_body_that_is_no_event(body: str, reason: str) -> None:
    signature = hmac.new(SECRET.encode(), f"1000.{body}".encode(), hashlib.sha256).hexdigest()
    with pytest.raises(SignatureError, match=reason):
        WebhookVerifier(SECRET, clock=At(1000)).verify(body, f"t=1000,v1={signature}")


def test_uses_the_system_clock_by_default_so_an_old_vector_is_refused() -> None:
    with pytest.raises(SignatureError, match="too old"):
        WebhookVerifier(SECRET).verify(PAID["body"], PAID["header"])


@pytest.mark.parametrize(("secret", "tolerance"), [("", 300), ("whsec_x", 0)])
def test_needs_a_secret_and_a_positive_tolerance(secret: str, tolerance: int) -> None:
    with pytest.raises(ValueError, match=r"secret|tolerance"):
        WebhookVerifier(secret, tolerance_seconds=tolerance)

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from stablevoy import InvoiceStatus

from .support import INVOICE_ID, answer, client, example


def test_creates_an_invoice_with_the_key_the_idempotency_key_and_json() -> None:
    created = example("POST", "/v1/invoices", 201)
    t = client(answer(201, created))
    result = t.client.invoices.create(
        1999, external_reference="order-1042", return_url="https://shop.example/thanks", idempotency_key="order-1042"
    )
    sent = t.opener.last
    assert (sent.method, sent.url) == ("POST", "https://api.stablevoy.com/v1/invoices")
    assert sent.headers["Authorization"] == "Bearer sk_test_key"
    assert sent.headers["Idempotency-key"] == "order-1042"
    assert sent.headers["Content-type"] == "application/json"
    assert sent.headers["User-agent"].startswith("stablevoy-python/1.0.1 Python/")
    assert sent.timeout == 30.0
    assert json.loads(sent.body or b"") == {
        "amountUsdCents": 1999,
        "externalReference": "order-1042",
        "returnUrl": "https://shop.example/thanks",
    }
    assert result.checkout_url == created["checkoutUrl"]
    assert result.invoice.id == created["id"]
    assert result.replayed == created["replayed"]
    assert result.invoice.expires_at.tzinfo is not None


def test_sends_only_the_fields_that_are_set() -> None:
    t = client(answer(201, example("POST", "/v1/invoices", 201)), answer(201, example("POST", "/v1/invoices", 201)))
    t.client.invoices.create(500)
    assert json.loads(t.opener.last.body or b"") == {"amountUsdCents": 500}
    assert "Idempotency-key" not in t.opener.last.headers
    t.client.invoices.create(700, external_reference="order-7")
    assert json.loads(t.opener.last.body or b"") == {"amountUsdCents": 700, "externalReference": "order-7"}


@pytest.mark.parametrize("amount", [0, -1, 19.99, True, "1999"])
def test_refuses_an_amount_that_is_no_positive_whole_number(amount: object) -> None:
    t = client()
    with pytest.raises(ValueError, match="positive whole number"):
        t.client.invoices.create(amount)  # type: ignore[arg-type]
    assert t.opener.sent == []


def test_reads_an_invoice_with_its_payments() -> None:
    invoice = example("GET", "/v1/invoices/{invoiceId}", 200)
    payment = {
        "id": INVOICE_ID,
        "network": "tron",
        "amountDueUsdCents": 1500,
        "token": "USDT",
        "amount": "15000042",
        "txHash": "ab" * 32,
        "status": "confirmed",
        "screeningStatus": "clear",
        "detectedAt": "2026-10-25T10:00:00.000Z",
    }
    t = client(answer(200, {**invoice, "payments": [payment], "status": "paid"}))
    result = t.client.invoices.get(INVOICE_ID)
    assert t.opener.last.url == f"https://api.stablevoy.com/v1/invoices/{INVOICE_ID}"
    assert result.id == invoice["id"]
    assert result.is_paid()
    assert result.payments[0].detected_at == datetime(2026, 10, 25, 10, 0, tzinfo=UTC)
    assert result.payments[0].amount == "15000042"
    assert len(result.deposit_addresses) == len(invoice["depositAddresses"])  # type: ignore[arg-type]


@pytest.mark.parametrize("invoice_id", ["..", "../stores", "x?status=paid", "", INVOICE_ID[:-1], INVOICE_ID + "\n"])
def test_refuses_an_invoice_id_that_is_no_uuid_before_sending_anything(invoice_id: str) -> None:
    t = client()
    with pytest.raises(ValueError, match="UUID"):
        t.client.invoices.get(invoice_id)
    assert t.opener.sent == []


def test_lists_a_page_with_its_filters_and_by_default_fifty() -> None:
    page = example("GET", "/v1/invoices", 200)
    t = client(answer(200, page), answer(200, {"items": [], "nextCursor": None}))
    result = t.client.invoices.list(limit=20, cursor="cursor-1", status=InvoiceStatus.PAID)
    assert t.opener.last.url == "https://api.stablevoy.com/v1/invoices?limit=20&cursor=cursor-1&status=paid"
    assert len(result.items) > 0
    t.client.invoices.list()
    assert t.opener.last.url == "https://api.stablevoy.com/v1/invoices?limit=50"


@pytest.mark.parametrize("limit", [0, 101])
def test_refuses_a_page_size_outside_one_to_a_hundred(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        client().client.invoices.list(limit=limit)


def test_walks_every_page() -> None:
    invoice = example("GET", "/v1/invoices/{invoiceId}", 200)
    t = client(answer(200, {"items": [invoice, invoice], "nextCursor": "next"}), answer(200, {"items": [invoice], "nextCursor": None}))
    assert len(list(t.client.invoices.all(status=InvoiceStatus.EXPIRED, page_size=2))) == 3
    assert [s.url for s in t.opener.sent] == [
        "https://api.stablevoy.com/v1/invoices?limit=2&status=expired",
        "https://api.stablevoy.com/v1/invoices?limit=2&cursor=next&status=expired",
    ]


def test_invoice_status_tells_which_orders_can_be_fulfilled() -> None:
    assert [
        s for s in ("awaiting_payment", "paid", "overpaid", "paid_late", "underpaid", "expired", "on_hold") if InvoiceStatus.is_paid(s)
    ] == [
        "paid",
        "overpaid",
        "paid_late",
    ]

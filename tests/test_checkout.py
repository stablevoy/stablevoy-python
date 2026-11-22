from __future__ import annotations

from datetime import datetime

import pytest

from stablevoy import CheckoutStep, CheckoutSurface, CheckoutTrailStep, SummaryPeriod, UnexpectedResponseError

from .support import answer, client, example

FUNNEL_PATH = "/v1/store/checkout-funnel"
TRAIL_PATH = "/v1/invoices/{invoiceId}/checkout-trail"
INVOICE = "7c3360b5-e8cc-4775-8a13-7324d4f1296e"


def test_asks_for_the_keys_store_and_reads_every_count() -> None:
    funnel = example("GET", FUNNEL_PATH, 200)
    t = client(answer(200, funnel))
    result = t.client.stores.checkout_funnel(period=SummaryPeriod.LAST_30_DAYS)
    assert t.opener.last.url == "https://api.stablevoy.com/v1/store/checkout-funnel?period=last_30_days"
    assert (result.created_from, result.created_to, result.invoices, result.detected, result.paid) == (
        funnel["createdFrom"],
        funnel["createdTo"],
        funnel["invoices"],
        funnel["detected"],
        funnel["paid"],
    )
    assert dict(result.steps) == funnel["steps"]
    assert dict(result.opened_on) == funnel["openedOn"]
    steps = funnel["steps"]
    opened_on = funnel["openedOn"]
    assert isinstance(steps, dict)
    assert isinstance(opened_on, dict)
    assert result.steps[CheckoutStep.OPENED] == steps["opened"]
    assert result.opened_on[CheckoutSurface.WIDGET] == opened_on["widget"]


def test_asks_for_own_days() -> None:
    t = client(answer(200, example("GET", FUNNEL_PATH, 200)))
    t.client.stores.checkout_funnel(created_from="2026-11-01", created_to="2026-11-30")
    assert t.opener.last.url == "https://api.stablevoy.com/v1/store/checkout-funnel?createdFrom=2026-11-01&createdTo=2026-11-30"


@pytest.mark.parametrize(
    ("period", "created_from", "created_to"),
    [(None, None, None), ("last_year", None, None), (None, "2026-11-01", None), ("last_7_days", None, "2026-11-30")],
)
def test_refuses_a_bad_range_before_sending_anything(period: str | None, created_from: str | None, created_to: str | None) -> None:
    t = client()
    with pytest.raises(ValueError, match=r"period|created_"):
        t.client.stores.checkout_funnel(period=period, created_from=created_from, created_to=created_to)
    assert t.opener.sent == []


@pytest.mark.parametrize("field", ["steps", "paid"])
def test_refuses_a_funnel_without_a_field(field: str) -> None:
    funnel = example("GET", FUNNEL_PATH, 200)
    del funnel[field]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, funnel)).client.stores.checkout_funnel(period=SummaryPeriod.THIS_MONTH)


def test_refuses_a_count_that_is_not_a_whole_number() -> None:
    funnel = example("GET", FUNNEL_PATH, 200)
    steps = funnel["steps"]
    assert isinstance(steps, dict)
    steps["opened"] = "31"
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, funnel)).client.stores.checkout_funnel(period=SummaryPeriod.THIS_MONTH)


def test_reads_the_steps_of_one_invoice_with_their_times() -> None:
    trail = example("GET", TRAIL_PATH, 200)
    t = client(answer(200, trail))
    result = t.client.invoices.checkout_trail(INVOICE)
    assert t.opener.last.url == f"https://api.stablevoy.com/v1/invoices/{INVOICE}/checkout-trail"
    steps = trail["steps"]
    assert isinstance(steps, list)
    assert result.invoice_id == trail["invoiceId"]
    assert result.steps == tuple(CheckoutTrailStep(s["step"], datetime.fromisoformat(s["at"]), s["surface"]) for s in steps)


def test_keeps_a_step_this_library_does_not_know_yet() -> None:
    trail = {"invoiceId": INVOICE, "steps": [{"step": "refunded", "at": "2026-11-20T14:01:12.000Z", "surface": None}]}
    assert client(answer(200, trail)).client.invoices.checkout_trail(INVOICE).steps[0].step == "refunded"


@pytest.mark.parametrize("invoice_id", ["../store", "not-a-uuid", ""])
def test_refuses_a_bad_invoice_id_before_sending_anything(invoice_id: str) -> None:
    t = client()
    with pytest.raises(ValueError, match="UUID"):
        t.client.invoices.checkout_trail(invoice_id)
    assert t.opener.sent == []


def test_refuses_a_step_without_a_valid_time() -> None:
    trail = {"invoiceId": INVOICE, "steps": [{"step": "created", "at": "yesterday", "surface": None}]}
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, trail)).client.invoices.checkout_trail(INVOICE)

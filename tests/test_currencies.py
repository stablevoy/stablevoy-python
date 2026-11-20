from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from stablevoy import ApiError, UnexpectedResponseError

from .support import INVOICE_ID, answer, client, example, example_value

PRICING = {
    "currency": "EUR",
    "amount": 4999,
    "exponent": 2,
    "usdPerUnit": "1.0992",
    "rateSource": "ecb",
    "rateAt": "2026-11-19T15:00:00.000Z",
}


def test_creates_an_invoice_priced_in_eur_and_reads_the_price_and_the_rate() -> None:
    created = {**example("POST", "/v1/invoices", 201), "amountUsdCents": 5495, "pricing": PRICING}
    t = client(answer(201, created))
    result = t.client.invoices.create(amount=4999, currency="EUR", external_reference="order-1")
    assert json.loads(t.opener.last.body or b"") == {"amount": 4999, "currency": "EUR", "externalReference": "order-1"}
    assert result.invoice.amount_usd_cents == 5495
    p = result.invoice.pricing
    assert p is not None
    assert (p.currency, p.amount, p.exponent, p.usd_per_unit, p.rate_source) == ("EUR", 4999, 2, "1.0992", "ecb")
    assert p.rate_at == datetime(2026, 11, 19, 15, 0, tzinfo=UTC)


def test_reads_a_usd_invoice_and_an_old_payload_without_pricing() -> None:
    usd = example("GET", "/v1/invoices/{invoiceId}", 200)
    old = {k: v for k, v in usd.items() if k != "pricing"}
    t = client(answer(200, usd), answer(200, old))
    assert t.client.invoices.get(INVOICE_ID).pricing is None
    assert t.client.invoices.get(INVOICE_ID).pricing is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"amount_usd_cents": 100, "amount": 100, "currency": "EUR"},
        {"amount_usd_cents": 100, "currency": "EUR"},
        {},
        {"amount": 100},
        {"currency": "EUR"},
        {"amount": 0, "currency": "EUR"},
        {"amount": 10.5, "currency": "EUR"},
        {"amount": True, "currency": "EUR"},
        {"amount": 100, "currency": "eur"},
        {"amount": 100, "currency": 978},
    ],
)
def test_refuses_an_amount_of_the_wrong_shape_before_sending(kwargs: dict[str, object]) -> None:
    t = client()
    with pytest.raises(ValueError, match=r"amount|currency"):
        t.client.invoices.create(**kwargs)  # type: ignore[arg-type]
    assert t.opener.sent == []


def test_lists_the_currencies_and_those_of_a_store_with_its_own_rates() -> None:
    every = example_value("GET", "/v1/currencies", 200)
    mine = example_value("GET", "/v1/stores/{storeId}/currencies", 200)
    assert isinstance(every, list)
    t = client(answer(200, every), answer(200, mine))
    found = t.client.currencies.list()
    assert t.opener.last.url == "https://api.stablevoy.com/v1/currencies"
    assert len(found) == len(every)
    usd = next(c for c in found if c.code == "USD")
    assert (usd.market, usd.store, usd.effective and usd.effective.source) == (None, None, "usd")
    eur = next(c for c in found if c.code == "EUR")
    assert eur.market is not None
    assert eur.market.usable
    own = next(c for c in t.client.currencies.for_store(INVOICE_ID) if c.code == "EUR")
    assert t.opener.last.url == f"https://api.stablevoy.com/v1/stores/{INVOICE_ID}/currencies"
    assert own.effective is not None
    assert own.effective.source == "merchant"
    assert own.store is not None
    assert not own.store.diverges_from_market
    assert own.store.set_at == datetime(2026, 11, 19, 16, 20, tzinfo=UTC)


def test_reads_a_currency_that_prices_no_invoice_right_now() -> None:
    stale = {
        "code": "GBP",
        "exponent": 2,
        "market": {"usdPerUnit": "1.3", "source": "ecb", "rateAt": "2026-11-01T15:00:00.000Z", "usable": False},
        "store": None,
        "effective": None,
    }
    t = client(answer(200, [stale]))
    (gbp,) = t.client.currencies.list()
    assert gbp.effective is None
    assert gbp.market is not None
    assert not gbp.market.usable


def test_refuses_a_store_id_that_is_not_a_uuid_and_an_answer_that_is_not_a_list() -> None:
    t = client(answer(200, {"not": "a list"}))
    with pytest.raises(ValueError, match="UUID"):
        t.client.currencies.for_store("../me")
    assert t.opener.sent == []
    with pytest.raises(UnexpectedResponseError):
        t.client.currencies.list()


def test_names_the_new_error_codes() -> None:
    assert (ApiError.EXCHANGE_RATE_UNAVAILABLE, ApiError.CURRENCY_NOT_SUPPORTED) == ("exchange_rate_unavailable", "currency_not_supported")

from __future__ import annotations

from datetime import datetime

import pytest

from stablevoy import ApiError, NetworkTotal, SummaryPeriod, UnexpectedResponseError

from .support import answer, client, example, example_value, problem


def test_asks_for_a_period_and_reads_the_totals() -> None:
    summary = example("GET", "/v1/invoices/summary", 200)
    t = client(answer(200, summary))
    result = t.client.invoices.summary(period=SummaryPeriod.LAST_7_DAYS)
    assert t.opener.last.url == "https://api.stablevoy.com/v1/invoices/summary?period=last_7_days"
    invoices = summary["invoices"]
    assert isinstance(invoices, dict)
    assert (result.created_from, result.created_to) == (summary["createdFrom"], summary["createdTo"])
    assert result.invoice_count == invoices["count"]
    assert dict(result.invoices_by_status) == invoices["byStatus"]
    assert result.invoiced_usd_cents == summary["invoicedUsdCents"]
    assert result.received_usd_micros == summary["receivedUsdMicros"]
    by_network = summary["byNetwork"]
    assert isinstance(by_network, list)
    assert result.by_network == tuple(NetworkTotal(n["network"], n["token"], n["payments"], n["receivedUsdMicros"]) for n in by_network)


def test_asks_for_own_days() -> None:
    t = client(answer(200, example("GET", "/v1/invoices/summary", 200)))
    t.client.invoices.summary(created_from="2026-10-01", created_to="2026-10-31")
    assert t.opener.last.url == "https://api.stablevoy.com/v1/invoices/summary?createdFrom=2026-10-01&createdTo=2026-10-31"


@pytest.mark.parametrize(
    ("period", "created_from", "created_to"),
    [
        (None, None, None),
        ("last_7_days", "2026-10-01", "2026-10-31"),
        ("last_year", None, None),
        (None, "2026-10-01", None),
        (None, None, "2026-10-31"),
        (None, "1.10.2026", "2026-10-31"),
    ],
)
def test_refuses_a_bad_range_before_sending_anything(period: str | None, created_from: str | None, created_to: str | None) -> None:
    t = client()
    with pytest.raises(ValueError, match=r"period|created_"):
        t.client.invoices.summary(period=period, created_from=created_from, created_to=created_to)
    assert t.opener.sent == []


def test_passes_on_the_refusal_of_a_range_over_92_days() -> None:
    t = client(answer(400, problem(400, "invalid_invoice_filter", "createdFrom and createdTo are at most 92 days apart")))
    with pytest.raises(ApiError) as raised:
        t.client.invoices.summary(created_from="2026-01-01", created_to="2026-12-31")
    assert raised.value.code == ApiError.INVALID_INVOICE_FILTER


def test_refuses_a_summary_without_the_counts() -> None:
    summary = example("GET", "/v1/invoices/summary", 200)
    del summary["invoices"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, summary)).client.invoices.summary(period=SummaryPeriod.THIS_MONTH)


def test_lists_the_unmatched_transfers_of_the_store() -> None:
    transfers = example_value("GET", "/v1/unmatched-transfers", 200)
    assert isinstance(transfers, list)
    t = client(answer(200, transfers))
    result = t.client.unmatched_transfers.list()
    assert t.opener.last.url == "https://api.stablevoy.com/v1/unmatched-transfers"
    assert len(result) == len(transfers)
    first = transfers[0]
    got = result[0]
    assert (got.id, got.network, got.network_name, got.payout_address, got.from_address) == (
        first["id"],
        first["network"],
        first["networkName"],
        first["payoutAddress"],
        first["fromAddress"],
    )
    assert (got.tx_hash, got.token_symbol, got.amount_usd_micros, got.explorer_tx_url, got.shared_with_stores) == (
        first["txHash"],
        first["tokenSymbol"],
        first["amountUsdMicros"],
        first["explorerTxUrl"],
        first["sharedWithStores"],
    )
    assert got.detected_at == datetime.fromisoformat(first["detectedAt"])


def test_refuses_an_unmatched_answer_that_is_not_a_list_or_a_transfer_without_shared_with_stores() -> None:
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, {})).client.unmatched_transfers.list()
    transfers = example_value("GET", "/v1/unmatched-transfers", 200)
    assert isinstance(transfers, list)
    del transfers[0]["sharedWithStores"]
    with pytest.raises(UnexpectedResponseError, match=r"unmatchedTransfers\[0\]\.sharedWithStores is missing"):
        client(answer(200, transfers)).client.unmatched_transfers.list()


def test_reads_the_per_store_limits_and_refuses_limits_without_them() -> None:
    limits = example("GET", "/v1/limits", 200)
    result = client(answer(200, limits)).client.platform.limits()
    keys = limits["apiKeysPerStore"]
    assert isinstance(keys, dict)
    per_store = result.api_keys_per_store
    assert (per_store.plugin, per_store.mcp, per_store.api) == (keys["plugin"], keys["mcp"], keys["api"])
    assert result.open_invoices_per_store == limits["openInvoicesPerStore"]
    assert result.invoices_per_minute_per_store == limits["invoicesPerMinutePerStore"]
    assert ApiError.OPEN_INVOICE_LIMIT_REACHED == "open_invoice_limit_reached"
    del limits["openInvoicesPerStore"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, limits)).client.platform.limits()

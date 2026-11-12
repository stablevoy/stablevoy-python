from __future__ import annotations

from datetime import UTC, datetime

import pytest

from stablevoy import ApiError, PayoutSources, Store, UnexpectedResponseError

from .support import answer, client, example, example_value


def test_reads_the_store_of_the_key() -> None:
    store = example("GET", "/v1/store", 200)
    t = client(answer(200, store))
    result = t.client.stores.current()
    assert t.opener.last.url == "https://api.stablevoy.com/v1/store"
    assert result.name == store["name"]
    assert list(result.enabled_networks) == store["enabledNetworks"]
    assert result.networks_without_payout == ()
    assert result.can_accept_payments()


def test_tells_whether_any_enabled_network_has_a_payout_wallet() -> None:
    def read(missing: list[str]) -> Store:
        body = {**example("GET", "/v1/store", 200), "enabledNetworks": ["base", "tron"], "networksWithoutPayout": missing}
        return client(answer(200, body)).client.stores.current()

    assert read(["tron"]).networks_without_payout == ("tron",)
    assert read(["tron"]).can_accept_payments()
    assert not read(["base", "tron"]).can_accept_payments()
    assert ApiError.PAYOUT_ADDRESS_NOT_SET == "payout_address_not_set"


def test_reads_the_evm_payout_status_and_the_networks_it_blocks() -> None:
    store = example("GET", "/v1/store", 200)
    plain = client(answer(200, store)).client.stores.current()
    assert plain.evm_payout_status == store["evmPayoutStatus"]
    assert plain.evm_networks_blocked == ()
    assert not plain.evm_payout_needs_review()

    def read(**fields: object) -> Store:
        body = {**store, "enabledNetworks": ["base", "tron"], "networksWithoutPayout": [], **fields}
        return client(answer(200, body)).client.stores.current()

    blocked = read(evmPayoutStatus=Store.EVM_PAYOUT_UNACKNOWLEDGED, evmNetworksBlocked=["base"])
    assert blocked.evm_payout_needs_review()
    assert blocked.evm_networks_blocked == ("base",)
    assert blocked.can_accept_payments()
    assert not read(evmPayoutStatus="unacknowledged", evmNetworksBlocked=["base"], networksWithoutPayout=["tron"]).can_accept_payments()
    assert read(evmPayoutStatus=None).evm_payout_status is None
    assert ApiError.PAYOUT_ADDRESS_UNACKNOWLEDGED == "payout_address_unacknowledged"


def test_reads_the_payout_addresses_of_the_account() -> None:
    store = example("GET", "/v1/store", 200)
    result = client(answer(200, {**store, "payoutAddresses": {"evm": "0x" + "ab" * 20, "tron": None}})).client.stores.current()
    assert (result.payout_addresses.evm, result.payout_addresses.tron) == ("0x" + "ab" * 20, None)
    del store["payoutAddresses"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, store)).client.stores.current()


def test_reads_where_each_payout_wallet_comes_from_the_account_wallets_and_the_archive_date() -> None:
    store = example("GET", "/v1/store", 200)
    changed = {
        **store,
        "payoutSources": {"evm": PayoutSources.STORE, "tron": None},
        "accountPayoutAddresses": {"evm": "0x" + "cd" * 20, "tron": None},
        "archivedAt": "2026-11-10T10:00:00.000Z",
    }
    result = client(answer(200, changed)).client.stores.current()
    assert (result.payout_sources.evm, result.payout_sources.tron) == ("store", None)
    assert result.account_payout_addresses.evm == "0x" + "cd" * 20
    assert result.archived_at == datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
    assert client(answer(200, store)).client.stores.current().archived_at is None


@pytest.mark.parametrize("field", ["payoutSources", "accountPayoutAddresses", "archivedAt"])
def test_refuses_a_store_without_the_new_payout_fields(field: str) -> None:
    store = example("GET", "/v1/store", 200)
    del store[field]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, store)).client.stores.current()


def test_reads_the_payment_window_of_the_store_none_for_the_platform_default() -> None:
    store = example("GET", "/v1/store", 200)
    assert client(answer(200, store)).client.stores.current().invoice_lifetime_minutes is None
    assert client(answer(200, {**store, "invoiceLifetimeMinutes": 1440})).client.stores.current().invoice_lifetime_minutes == 1440
    del store["invoiceLifetimeMinutes"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, store)).client.stores.current()


def test_reads_the_invoice_lifetime_from_the_limits() -> None:
    limits = example("GET", "/v1/limits", 200)
    result = client(answer(200, limits)).client.platform.limits()
    assert (result.default_invoice_lifetime_minutes, result.min_invoice_lifetime_minutes, result.max_invoice_lifetime_minutes) == (
        limits["defaultInvoiceLifetimeMinutes"],
        limits["minInvoiceLifetimeMinutes"],
        limits["maxInvoiceLifetimeMinutes"],
    )
    assert ApiError.INVALID_INVOICE_LIFETIME == "invalid_invoice_lifetime"


def test_refuses_a_store_without_the_evm_payout_fields() -> None:
    old = dict(example("GET", "/v1/store", 200))
    del old["evmNetworksBlocked"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, old)).client.stores.current()


def test_refuses_a_store_without_the_payout_field() -> None:
    old = dict(example("GET", "/v1/store", 200))
    del old["networksWithoutPayout"]
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, old)).client.stores.current()


def test_reads_limits_pricing_and_networks() -> None:
    t = client(
        answer(200, example("GET", "/v1/limits", 200)),
        answer(200, example("GET", "/v1/pricing", 200)),
        answer(200, example_value("GET", "/v1/networks", 200)),
    )
    assert t.client.platform.limits().max_invoice_usd_cents > 0
    assert t.client.platform.pricing().fee_bps >= 0
    networks = t.client.platform.networks()
    assert networks
    assert networks[0].tokens
    first = example_value("GET", "/v1/networks", 200)
    assert isinstance(first, list)
    assert isinstance(first[0], dict)
    assert (networks[0].forwarder_implementation, networks[0].explorer_address_url, networks[0].rpc_url) == (
        first[0]["forwarderImplementation"],
        first[0]["explorerAddressUrl"],
        first[0]["rpcUrl"],
    )


def test_names_the_plugin_connected_to_the_store() -> None:
    connected = client(answer(200, {**example("GET", "/v1/store", 200), "connectedPlatform": "woocommerce"})).client.stores.current()
    assert connected.connected_platform == "woocommerce"
    assert client(answer(200, example("GET", "/v1/store", 200))).client.stores.current().connected_platform is None


def test_refuses_networks_that_are_not_a_list() -> None:
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, {"key": "base"})).client.platform.networks()

from __future__ import annotations

import pytest

from stablevoy import UnexpectedResponseError

from .support import answer, client, example, example_value


def test_reads_the_store_of_the_key() -> None:
    store = example("GET", "/v1/store", 200)
    t = client(answer(200, store))
    result = t.client.stores.current()
    assert t.opener.last.url == "https://api.stablevoy.com/v1/store"
    assert result.name == store["name"]
    assert list(result.enabled_networks) == store["enabledNetworks"]


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


def test_refuses_networks_that_are_not_a_list() -> None:
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, {"key": "base"})).client.platform.networks()

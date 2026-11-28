from __future__ import annotations

import pytest

from stablevoy import CheckoutLink, CreatedInvoice, PayoutAnchor, PayoutMismatchError, UnexpectedResponseError
from stablevoy.model.fields import Fields
from tests.support import example

EVM = "0x5cc5bc5cc5bc5cc5bc5cc5bc5cc5bc5cc5bc5cc5"
TRON = "TJRabPrwbZy45sbavfcjinPJC18kjpRTv8"


def created(evm_payout: str, tron_payout: str | None = None, checkout_url: str | None = None) -> CreatedInvoice:
    """The documented answer of POST /v1/invoices, with the payout wallets set per network."""
    data = example("POST", "/v1/invoices", 201)
    addresses = data["depositAddresses"]
    assert isinstance(addresses, list)
    first = addresses[0]
    assert isinstance(first, dict)
    chosen = [{**first, "network": "base", "payoutAddress": evm_payout}]
    if tron_payout is not None:
        chosen.append({**first, "network": "tron", "address": tron_payout, "payoutAddress": tron_payout})
    data["depositAddresses"] = chosen
    if checkout_url is not None:
        data["checkoutUrl"] = checkout_url
    return CreatedInvoice.from_fields(Fields.of(data, "invoice"))


def test_builds_the_fragment() -> None:
    assert PayoutAnchor(evm=EVM, tron=TRON).fragment() == f"payout=evm:{EVM};tron:{TRON}"
    assert PayoutAnchor(tron=TRON).fragment() == f"payout=tron:{TRON}"
    assert PayoutAnchor(evm=EVM).evm == EVM
    assert PayoutAnchor(evm=EVM).tron is None


@pytest.mark.parametrize(("evm", "tron"), [(None, None), ("0x12", None), (None, "T123"), (EVM + "ff", None)])
def test_refuses_what_is_not_a_wallet(evm: str | None, tron: str | None) -> None:
    with pytest.raises(ValueError, match="payout"):
        PayoutAnchor(evm=evm, tron=tron)


def test_compares_evm_without_case_and_tron_exactly() -> None:
    anchor = PayoutAnchor(evm="0x" + EVM[2:].upper(), tron=TRON)
    assert anchor.accepts(EVM)
    assert anchor.accepts(TRON)
    assert not anchor.accepts(TRON.lower())
    assert not PayoutAnchor(tron=TRON).accepts(EVM)
    assert not PayoutAnchor(evm=EVM).accepts(TRON)
    assert not anchor.accepts("not an address")


def test_builds_the_link_from_the_site_and_the_invoice_id() -> None:
    invoice = created(EVM)
    link = CheckoutLink().for_invoice(invoice, PayoutAnchor(evm=EVM))
    assert link.url == f"https://stablevoy.com/pay/?i={invoice.invoice.id}#payout=evm:{EVM}"
    assert link.mismatched_networks == ()


def test_reports_changed_networks_and_stops_when_none_is_left() -> None:
    assert CheckoutLink().for_invoice(created(EVM, TRON), PayoutAnchor(evm=EVM)).mismatched_networks == ("tron",)
    other = "0x" + "99" * 20
    with pytest.raises(PayoutMismatchError, match=f"base: {other}"):
        CheckoutLink().for_invoice(created(other), PayoutAnchor(evm=EVM))


def test_refuses_a_payment_link_of_another_site() -> None:
    with pytest.raises(UnexpectedResponseError):
        CheckoutLink().for_invoice(created(EVM, checkout_url="https://evil.example/pay/?i=x"), PayoutAnchor(evm=EVM))


def test_takes_a_local_site() -> None:
    invoice = created(EVM, checkout_url="https://stablevoy.test:8443/pay/?i=x")
    assert (
        CheckoutLink("https://Stablevoy.test:8443")
        .for_invoice(invoice, PayoutAnchor(evm=EVM))
        .url.startswith("https://stablevoy.test:8443/pay/?i=")
    )


@pytest.mark.parametrize(
    "bad",
    [
        "http://stablevoy.com",
        "https://stablevoy.com/",
        "https://stablevoy.com/pay",
        "https://u@stablevoy.com",
        "https://stablevoy.com?x=1",
        "https://stablevoy.com#x",
        "https://stablevoy.com:443",
        "https://stablevoy.com:99999",
        "https://",
        "stablevoy.com",
    ],
)
def test_refuses_anything_but_a_bare_https_origin(bad: str) -> None:
    with pytest.raises(ValueError, match="bare https origin"):
        CheckoutLink(bad)

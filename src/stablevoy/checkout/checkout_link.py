from __future__ import annotations

from urllib.parse import quote, urlsplit

from stablevoy.checkout.anchored_link import AnchoredLink
from stablevoy.checkout.payout_anchor import PayoutAnchor
from stablevoy.errors.payout_mismatch_error import PayoutMismatchError
from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.model.created_invoice import CreatedInvoice


class CheckoutLink:
    """Builds the payment link of a new invoice with the shop's payout anchor. The link is built from the configured site
    and the invoice id, never taken from the answer as it is: a checkout_url of another site is refused, so a lying answer
    cannot send the buyer elsewhere. Networks whose wallet the anchor does not name are reported; with none left it raises."""

    def __init__(self, site_url: str = "https://stablevoy.com") -> None:
        origin = self._https_origin(site_url)
        # Only a bare origin: no path, query, fragment or user part, so the link cannot be bent to another place.
        if origin is None or origin != site_url.lower():
            raise ValueError("site_url must be a bare https origin such as https://stablevoy.com")
        self._site_url = origin

    @staticmethod
    def _https_origin(site_url: str) -> str | None:
        try:
            parts = urlsplit(site_url)
            port = parts.port
        except ValueError:
            return None
        if parts.scheme != "https" or not parts.hostname:
            return None
        return f"https://{parts.hostname}" + (f":{port}" if port is not None and port != 443 else "")

    def for_invoice(self, created: CreatedInvoice, anchor: PayoutAnchor) -> AnchoredLink:
        if not created.checkout_url.startswith(self._site_url + "/"):
            raise UnexpectedResponseError(f"The payment link of the answer is not on {self._site_url}; refusing to send the buyer there")
        addresses = created.invoice.deposit_addresses
        mismatched = [a for a in addresses if not anchor.accepts(a.payout_address)]
        if addresses and len(mismatched) == len(addresses):
            wallets = ", ".join(f"{a.network}: {a.payout_address}" for a in mismatched)
            message = f"No network of the invoice pays to a wallet the shop confirmed ({anchor.fragment()}); the invoice pays to {wallets}"
            raise PayoutMismatchError(message)
        url = f"{self._site_url}/pay/?i={quote(created.invoice.id, safe='')}#{anchor.fragment()}"
        return AnchoredLink(url, tuple(a.network for a in mismatched))

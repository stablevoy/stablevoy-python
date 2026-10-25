from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields
from stablevoy.model.invoice import Invoice


@dataclass(frozen=True)
class CreatedInvoice:
    """The answer to creating an invoice: the invoice, the hosted payment page to send the buyer to, and what was left out."""

    invoice: Invoice
    checkout_url: str
    unavailable_networks: tuple[str, ...]
    replayed: bool

    @classmethod
    def from_fields(cls, f: Fields) -> CreatedInvoice:
        return cls(Invoice.from_fields(f), f.string("checkoutUrl"), f.strings("unavailableNetworks"), f.boolean("replayed"))

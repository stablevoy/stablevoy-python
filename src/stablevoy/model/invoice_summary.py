from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from stablevoy.model.fields import Fields
from stablevoy.model.network_total import NetworkTotal


@dataclass(frozen=True)
class InvoiceSummary:
    """Totals of the store's invoices created in a range of UTC days."""

    created_from: str
    """The first day counted, YYYY-MM-DD, also when a period was asked for."""
    created_to: str
    """The last day counted, included."""
    invoice_count: int
    invoices_by_status: Mapping[str, int]
    """How many of them are in each status now, every status included (see InvoiceStatus)."""
    invoiced_usd_cents: int
    """Sum of their amounts in US cents, cancelled and expired invoices left out."""
    received_usd_micros: str
    """The money that counts for them (confirmed and screened clear), in millionths of a dollar, as a string."""
    by_network: tuple[NetworkTotal, ...]

    @classmethod
    def from_fields(cls, f: Fields) -> InvoiceSummary:
        invoices = f.child("invoices")
        by_status = invoices.child("byStatus")
        return cls(
            f.string("createdFrom"),
            f.string("createdTo"),
            invoices.integer("count"),
            {status: by_status.integer(status) for status in by_status.raw()},
            f.integer("invoicedUsdCents"),
            f.string("receivedUsdMicros"),
            f.objects("byNetwork", NetworkTotal.from_fields),
        )

from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Limits:
    """The smallest and largest invoice the platform accepts, in US cents."""

    min_invoice_usd_cents: int
    max_invoice_usd_cents: int

    @classmethod
    def from_fields(cls, f: Fields) -> Limits:
        return cls(f.integer("minInvoiceUsdCents"), f.integer("maxInvoiceUsdCents"))

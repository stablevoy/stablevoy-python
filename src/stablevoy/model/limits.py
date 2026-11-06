from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Limits:
    """The smallest and largest invoice the platform accepts, in US cents, and how long an invoice can be paid, in minutes."""

    min_invoice_usd_cents: int
    max_invoice_usd_cents: int
    default_invoice_lifetime_minutes: int
    """The lifetime of an invoice when neither the request nor the store names one."""
    min_invoice_lifetime_minutes: int
    """The lower bound of expires_in_minutes and of a store's payment window."""
    max_invoice_lifetime_minutes: int
    """The upper bound of expires_in_minutes and of a store's payment window."""

    @classmethod
    def from_fields(cls, f: Fields) -> Limits:
        return cls(
            f.integer("minInvoiceUsdCents"),
            f.integer("maxInvoiceUsdCents"),
            f.integer("defaultInvoiceLifetimeMinutes"),
            f.integer("minInvoiceLifetimeMinutes"),
            f.integer("maxInvoiceLifetimeMinutes"),
        )

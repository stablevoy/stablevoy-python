from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class InvoiceRange:
    """
    The amounts an invoice of the store may have now, in US cents: the bounds of the account (the platform ones, or a
    higher or lower cap set for the account on request) narrowed by the store's own minimum and maximum. Use it to decide
    whether to offer the payment method; never compute it from platform.limits(), which shows only the platform default.
    """

    min_usd_cents: int
    max_usd_cents: int

    def contains(self, amount_usd_cents: int) -> bool:
        """True when an invoice of amount_usd_cents would be accepted by these bounds."""
        return self.min_usd_cents <= amount_usd_cents <= self.max_usd_cents

    @classmethod
    def from_fields(cls, f: Fields) -> InvoiceRange:
        return cls(f.integer("minUsdCents"), f.integer("maxUsdCents"))

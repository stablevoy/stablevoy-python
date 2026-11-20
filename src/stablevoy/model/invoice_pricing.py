from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class InvoicePricing:
    """
    The price of an invoice created in another currency than USD, and the rate that turned it into amount_usd_cents.
    Fixed when the invoice was created. amount is in the smallest unit of currency: 4999 with exponent 2 is 49.99 EUR.
    """

    currency: str
    """ISO 4217 code, one of currencies.list()."""
    amount: int
    exponent: int
    """Decimal places of currency: 2 for EUR, 0 for JPY."""
    usd_per_unit: str
    """US dollars for one unit of currency, a decimal string such as "1.0992"."""
    rate_source: str
    """'ecb' (ECB reference rate, checked against Coinbase) or 'merchant' (the store's own fixed rate)."""
    rate_at: datetime
    """When the rate was valid: the ECB publication time, or when the merchant set the store rate."""

    @classmethod
    def from_fields(cls, f: Fields) -> InvoicePricing:
        return cls(
            f.string("currency"),
            f.integer("amount"),
            f.integer("exponent"),
            f.string("usdPerUnit"),
            f.string("rateSource"),
            f.date("rateAt"),
        )

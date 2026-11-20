from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.currency_rate import CurrencyRate
from stablevoy.model.fields import Fields
from stablevoy.model.market_rate import MarketRate
from stablevoy.model.store_rate import StoreRate


@dataclass(frozen=True)
class Currency:
    """One currency an invoice can be priced in, with its rates (GET /v1/currencies, GET /v1/stores/{id}/currencies)."""

    code: str
    """ISO 4217 code."""
    exponent: int
    """Decimal places of the smallest unit: 2 for EUR (amount 1999 is 19.99), 0 for JPY."""
    market: MarketRate | None
    """None for USD and before the first refresh."""
    store: StoreRate | None
    """The store's own rate (store list only); None when the store uses the market rate."""
    effective: CurrencyRate | None
    """The rate an invoice created now would use; None: an invoice in this currency is refused right now."""

    @classmethod
    def from_fields(cls, f: Fields) -> Currency:
        market = f.nullable_child("market")
        store = f.nullable_child("store")
        effective = f.nullable_child("effective")
        return cls(
            f.string("code"),
            f.integer("exponent"),
            None if market is None else MarketRate.from_fields(market),
            None if store is None else StoreRate.from_fields(store),
            None if effective is None else CurrencyRate.from_fields(effective),
        )

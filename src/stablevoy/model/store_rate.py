from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class StoreRate:
    """A store's own fixed rate, set in the dashboard and used for every invoice of the store in that currency."""

    usd_per_unit: str
    set_at: datetime
    diverges_from_market: bool
    """True when it is more than 10% away from the market rate. It is still used."""

    @classmethod
    def from_fields(cls, f: Fields) -> StoreRate:
        return cls(f.string("usdPerUnit"), f.date("setAt"), f.boolean("divergesFromMarket"))

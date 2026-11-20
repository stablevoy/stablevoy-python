from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class MarketRate:
    """The market rate of a currency stored now. usable False: older than the platform allows, so it prices no invoice."""

    usd_per_unit: str
    source: str
    rate_at: datetime
    usable: bool

    @classmethod
    def from_fields(cls, f: Fields) -> MarketRate:
        return cls(f.string("usdPerUnit"), f.string("source"), f.date("rateAt"), f.boolean("usable"))

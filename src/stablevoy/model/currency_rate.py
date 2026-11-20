from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class CurrencyRate:
    """A rate in US dollars per unit, with where it came from ('ecb', 'merchant' or 'usd')."""

    usd_per_unit: str
    source: str

    @classmethod
    def from_fields(cls, f: Fields) -> CurrencyRate:
        return cls(f.string("usdPerUnit"), f.string("source"))

from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Token:
    """A stablecoin accepted on a network."""

    symbol: str
    address: str
    decimals: int

    @classmethod
    def from_fields(cls, f: Fields) -> Token:
        return cls(f.string("symbol"), f.string("address"), f.integer("decimals"))

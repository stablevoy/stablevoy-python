from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class NetworkTotal:
    """The received money on one network in one token."""

    network: str
    token: str
    """USDT or USDC."""
    payments: int
    received_usd_micros: str
    """Millionths of a dollar, as a string: "251200000" is $251.20."""

    @classmethod
    def from_fields(cls, f: Fields) -> NetworkTotal:
        return cls(f.string("network"), f.string("token"), f.integer("payments"), f.string("receivedUsdMicros"))

from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Pricing:
    """The live price list: the free volume per payout wallet, the fee and the cap written into the contracts (50 bps is 0.5%)."""

    free_volume_usd_cents: int
    fee_bps: int
    max_fee_bps: int

    @classmethod
    def from_fields(cls, f: Fields) -> Pricing:
        return cls(f.integer("freeVolumeUsdCents"), f.integer("feeBps"), f.integer("maxFeeBps"))

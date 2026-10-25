from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class DepositAddress:
    """Where the buyer pays on one network: a one-time deposit address, or on Tron the merchant's own wallet."""

    network: str
    address: str
    payout_address: str
    amount_due_usd_cents: int

    @classmethod
    def from_fields(cls, f: Fields) -> DepositAddress:
        return cls(f.string("network"), f.string("address"), f.string("payoutAddress"), f.integer("amountDueUsdCents"))

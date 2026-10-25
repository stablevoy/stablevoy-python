from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Payment:
    """A transfer to the invoice. The amount is in the token's smallest units, as a string: "19990000" is 19.99 USDC."""

    id: str
    network: str
    amount_due_usd_cents: int
    token: str
    amount: str
    tx_hash: str
    status: str
    screening_status: str
    detected_at: datetime

    @classmethod
    def from_fields(cls, f: Fields) -> Payment:
        return cls(
            f.string("id"),
            f.string("network"),
            f.integer("amountDueUsdCents"),
            f.string("token"),
            f.string("amount"),
            f.string("txHash"),
            f.string("status"),
            f.string("screeningStatus"),
            f.date("detectedAt"),
        )

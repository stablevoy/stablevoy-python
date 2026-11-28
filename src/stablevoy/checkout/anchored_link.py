from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnchoredLink:
    """A payment link with the shop's payout anchor, and the networks of the invoice whose wallet the anchor does not name
    (the payment page leaves them out: tell the merchant their payout wallet changed)."""

    url: str
    mismatched_networks: tuple[str, ...]

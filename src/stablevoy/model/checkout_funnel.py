from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class CheckoutFunnel:
    """Where buyers stop on the payment page, for the store's invoices created in a range of UTC days. Counts of invoices, not of visits."""

    created_from: str
    """The first day counted, YYYY-MM-DD, also when a period was asked for."""
    created_to: str
    """The last day counted, included."""
    invoices: int
    """Invoices created in the range."""
    steps: Mapping[str, int]
    """How many of them reached each step of the payment page at least once, by step name (see CheckoutStep)."""
    opened_on: Mapping[str, int]
    """Opened invoices by where the page ran (see CheckoutSurface)."""
    detected: int
    """Invoices with at least one payment seen on chain."""
    paid: int
    """Invoices paid in full, overpaid or paid late."""

    @classmethod
    def from_fields(cls, f: Fields) -> CheckoutFunnel:
        steps = f.child("steps")
        opened_on = f.child("openedOn")
        return cls(
            f.string("createdFrom"),
            f.string("createdTo"),
            f.integer("invoices"),
            {name: steps.integer(name) for name in steps.raw()},
            {name: opened_on.integer(name) for name in opened_on.raw()},
            f.integer("detected"),
            f.integer("paid"),
        )

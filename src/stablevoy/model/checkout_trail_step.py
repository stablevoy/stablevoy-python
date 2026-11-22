from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class CheckoutTrailStep:
    """One step of an invoice on the payment page."""

    step: str
    """See CheckoutStep."""
    at: datetime
    """When the step was first reached."""
    surface: str | None
    """Where the page ran (see CheckoutSurface), only on opened; None otherwise."""

    @classmethod
    def from_fields(cls, f: Fields) -> CheckoutTrailStep:
        return cls(f.string("step"), f.date("at"), f.nullable_string("surface"))

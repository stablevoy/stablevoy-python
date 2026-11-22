from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.checkout_trail_step import CheckoutTrailStep
from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class CheckoutTrail:
    """The steps one invoice went through, oldest first: created, what the payment page reported, the first payment seen and the outcome."""

    invoice_id: str
    steps: tuple[CheckoutTrailStep, ...]

    @classmethod
    def from_fields(cls, f: Fields) -> CheckoutTrail:
        return cls(f.string("invoiceId"), f.objects("steps", CheckoutTrailStep.from_fields))

from typing import Final


class InvoiceStatus:
    """
    Invoice statuses. An invoice's status is a plain string, so a status added by a newer API version is kept, not lost;
    compare it with these values.
    """

    AWAITING_PAYMENT: Final = "awaiting_payment"
    CONFIRMING: Final = "confirming"
    PAID: Final = "paid"
    OVERPAID: Final = "overpaid"
    UNDERPAID: Final = "underpaid"
    EXPIRED: Final = "expired"
    PAID_LATE: Final = "paid_late"
    ON_HOLD: Final = "on_hold"

    @staticmethod
    def is_paid(status: str) -> bool:
        """The order can be fulfilled: the full amount, or more, has arrived and is confirmed."""
        return status in (InvoiceStatus.PAID, InvoiceStatus.OVERPAID, InvoiceStatus.PAID_LATE)

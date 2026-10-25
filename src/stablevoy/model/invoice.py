from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.deposit_address import DepositAddress
from stablevoy.model.fields import Fields
from stablevoy.model.invoice_status import InvoiceStatus
from stablevoy.model.payment import Payment


@dataclass(frozen=True)
class Invoice:
    """An invoice as the API returns it. Amounts are integers in US cents."""

    id: str
    store_id: str
    status: str
    amount_usd_cents: int
    fee_bps: int
    invoice_salt: str
    external_reference: str | None
    return_url: str | None
    expires_at: datetime
    paid_at: datetime | None
    hold_reason: str | None
    created_at: datetime
    deposit_addresses: tuple[DepositAddress, ...]
    payments: tuple[Payment, ...]

    @classmethod
    def from_fields(cls, f: Fields) -> Invoice:
        return cls(
            f.string("id"),
            f.string("storeId"),
            f.string("status"),
            f.integer("amountUsdCents"),
            f.integer("feeBps"),
            f.string("invoiceSalt"),
            f.nullable_string("externalReference"),
            f.nullable_string("returnUrl"),
            f.date("expiresAt"),
            f.nullable_date("paidAt"),
            f.nullable_string("holdReason"),
            f.date("createdAt"),
            f.objects("depositAddresses", DepositAddress.from_fields),
            f.objects("payments", Payment.from_fields),
        )

    def is_paid(self) -> bool:
        """True once the order can be fulfilled (paid, overpaid or paid late)."""
        return InvoiceStatus.is_paid(self.status)

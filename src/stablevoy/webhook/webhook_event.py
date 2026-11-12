from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields
from stablevoy.model.invoice import Invoice


@dataclass(frozen=True)
class WebhookEvent:
    """
    A verified webhook. Types: invoice.paid, invoice.overpaid, invoice.underpaid, invoice.expired, invoice.paid_late,
    invoice.on_hold, invoice.cancelled, invoice.payment_flagged, store.payout_attention, api_key.leaked,
    webhook_secret.leaked and webhook.test. invoice.payment_flagged: a payment of a settled invoice was flagged by
    screening; the invoice keeps its status and ``data["payment"]`` holds the payment. store.payout_attention: the EVM
    payout wallet this store uses (its own or the account's) became unconfirmed or is fine again; ``invoice`` is None and
    ``data["payout"]`` holds status, source ("store" or "account"), blockedNetworks and dashboardUrl. Read
    stores.current() again for the current state. api_key.leaked: GitHub found an API key of the store in public code and
    it was revoked; webhook_secret.leaked: the same for the webhook signing secret, which the merchant rotates; ``invoice``
    is None for both. Deliveries can repeat: use ``id`` to process each event once.
    """

    id: str
    type: str
    created_at: datetime
    invoice: Invoice | None
    data: dict[str, object]

    @classmethod
    def from_fields(cls, f: Fields) -> WebhookEvent:
        event_type = f.string("type")
        data = f.child("data")
        invoice = Invoice.from_fields(data.child("invoice")) if event_type.startswith("invoice.") else None
        return cls(f.string("id"), event_type, f.date("createdAt"), invoice, data.raw())

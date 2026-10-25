from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Store:
    """The store the API key belongs to."""

    id: str
    name: str
    status: str
    enabled_networks: tuple[str, ...]
    min_invoice_usd_cents: int | None
    max_invoice_usd_cents: int | None
    webhook_url: str | None
    website_url: str | None
    default_return_url: str | None
    created_at: datetime

    @classmethod
    def from_fields(cls, f: Fields) -> Store:
        return cls(
            f.string("id"),
            f.string("name"),
            f.string("status"),
            f.strings("enabledNetworks"),
            f.nullable_integer("minInvoiceUsdCents"),
            f.nullable_integer("maxInvoiceUsdCents"),
            f.nullable_string("webhookUrl"),
            f.nullable_string("websiteUrl"),
            f.nullable_string("defaultReturnUrl"),
            f.date("createdAt"),
        )

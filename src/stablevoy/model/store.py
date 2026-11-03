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
    networks_without_payout: tuple[str, ...]
    """Enabled networks with no payout wallet for their family (EVM or Tron) on the account: buyers are not offered them."""
    connected_platform: str | None
    """The plugin connected to the store in one click (woocommerce, edd, whmcs), or None."""

    def can_accept_payments(self) -> bool:
        """
        False when no enabled network has a payout wallet: every invoice would be refused with payout_address_not_set.
        Check it before offering the payment method, and show the merchant networks_without_payout when it is not empty.
        """
        return any(key not in self.networks_without_payout for key in self.enabled_networks)

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
            f.strings("networksWithoutPayout"),
            f.nullable_string("connectedPlatform"),
        )

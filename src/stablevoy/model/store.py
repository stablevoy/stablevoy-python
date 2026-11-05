from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class Store:
    """The store the API key belongs to."""

    EVM_PAYOUT_PLAIN: ClassVar[str] = "plain"
    EVM_PAYOUT_ACKNOWLEDGED: ClassVar[str] = "acknowledged"
    EVM_PAYOUT_UNACKNOWLEDGED: ClassVar[str] = "unacknowledged"
    EVM_PAYOUT_UNCHECKED: ClassVar[str] = "unchecked"

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
    evm_payout_status: str | None
    """
    The EVM payout wallet as last read on every EVM network: plain (a regular wallet), acknowledged (a smart contract
    wallet or EIP-7702 delegation the merchant confirmed), unacknowledged (not confirmed, or changed since: the EVM
    networks are left out of new invoices until the merchant reviews it in the dashboard), unchecked (not read yet), or
    None when the account has no EVM payout wallet.
    """
    evm_networks_blocked: tuple[str, ...]
    """Enabled EVM networks new invoices leave out because evm_payout_status is unacknowledged; empty otherwise."""

    def can_accept_payments(self) -> bool:
        """
        False when no enabled network can be paid: none has a payout wallet (invoices are refused with
        payout_address_not_set), or the only ones left are EVM networks blocked by an unconfirmed EVM payout wallet
        (payout_address_unacknowledged). Check it before offering the payment method, and show the merchant
        networks_without_payout and evm_networks_blocked when they are not empty.
        """
        return any(key not in self.networks_without_payout and key not in self.evm_networks_blocked for key in self.enabled_networks)

    def evm_payout_needs_review(self) -> bool:
        """
        True while the EVM payout wallet is not confirmed in the Stablevoy dashboard: show the merchant
        evm_networks_blocked and send them to the dashboard. A store.payout_attention webhook tells when this changes.
        """
        return self.evm_payout_status == self.EVM_PAYOUT_UNACKNOWLEDGED

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
            f.nullable_string("evmPayoutStatus"),
            f.strings("evmNetworksBlocked"),
        )

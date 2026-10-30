from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class InvoiceSource:
    """Where an invoice came from (``source`` on an Invoice)."""

    PAYMENT_LINK: ClassVar[str] = "payment_link"
    """Made in the dashboard as a payment link."""
    PLUGIN: ClassVar[str] = "plugin"
    """Made by a plugin connected in one click; ``platform`` names it."""
    API_KEY: ClassVar[str] = "api_key"
    """Made with an API key created by hand, such as your own code."""
    NOT_RECORDED: ClassVar[str] = "not_recorded"
    """Made before sources were recorded (31 October 2026)."""

    WOOCOMMERCE: ClassVar[str] = "woocommerce"
    EDD: ClassVar[str] = "edd"
    WHMCS: ClassVar[str] = "whmcs"

    kind: str
    """One of PAYMENT_LINK, PLUGIN, API_KEY, NOT_RECORDED; a kind added by a newer API version is kept as it is."""
    platform: str | None
    """The plugin, for PLUGIN."""
    api_key_id: str | None
    """The key that made the invoice, for PLUGIN and API_KEY."""
    api_key_name: str | None
    """The key's name, for API_KEY."""

    @classmethod
    def from_nullable_fields(cls, f: Fields | None) -> InvoiceSource:
        """The API sends null for an invoice made before sources were recorded."""
        if f is None:
            return cls(cls.NOT_RECORDED, None, None, None)
        kind = f.string("kind")
        return cls(
            kind,
            f.string("platform") if kind == cls.PLUGIN else None,
            f.string("apiKeyId") if kind in (cls.PLUGIN, cls.API_KEY) else None,
            f.string("apiKeyName") if kind == cls.API_KEY else None,
        )

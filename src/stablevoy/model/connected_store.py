from __future__ import annotations

from dataclasses import dataclass

from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class ConnectedStore:
    """What a redeemed connect code gives the shop: its API key, its webhook signing secret and the store they belong to."""

    api_key: str
    webhook_secret: str
    store_id: str
    store_name: str

    @classmethod
    def from_fields(cls, f: Fields) -> ConnectedStore:
        api_key = f.string("apiKey")
        if not api_key.startswith(("sk_live_", "sk_test_")):
            raise UnexpectedResponseError(f"{f.path_of('apiKey')} is not an API key (sk_live_ or sk_test_)")
        secret = f.string("webhookSecret")
        if not secret.startswith("whsec_"):
            raise UnexpectedResponseError(f"{f.path_of('webhookSecret')} is not a webhook secret (whsec_)")
        store = f.child("store")
        return cls(api_key, secret, store.string("id"), store.string("name"))

from __future__ import annotations

from dataclasses import dataclass

from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.keys.key_check import KeyCheck
from stablevoy.keys.key_format import check_api_key, check_webhook_secret
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
        if check_api_key(api_key) is not KeyCheck.OK:
            older = "or the older sk_live_, sk_test_"
            raise UnexpectedResponseError(f"{f.path_of('apiKey')} is not an API key (svk_live_, svk_test_, {older})")
        secret = f.string("webhookSecret")
        if check_webhook_secret(secret) is not KeyCheck.OK:
            raise UnexpectedResponseError(f"{f.path_of('webhookSecret')} is not a webhook secret (svwhsec_, or the older whsec_)")
        store = f.child("store")
        return cls(api_key, secret, store.string("id"), store.string("name"))

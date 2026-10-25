from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields
from stablevoy.model.token import Token


@dataclass(frozen=True)
class Network:
    """A network the platform accepts payments on: settlement is "forwarder" (deposit contracts) or "direct" (Tron)."""

    key: str
    display_name: str
    family: str
    chain_id: int
    confirmations: int
    settlement: str
    factory_address: str | None
    explorer_url: str | None
    tokens: tuple[Token, ...]

    @classmethod
    def from_fields(cls, f: Fields) -> Network:
        return cls(
            f.string("key"),
            f.string("displayName"),
            f.string("family"),
            f.integer("chainId"),
            f.integer("confirmations"),
            f.string("settlement"),
            f.nullable_string("factoryAddress"),
            f.nullable_string("explorerUrl"),
            f.objects("tokens", Token.from_fields),
        )

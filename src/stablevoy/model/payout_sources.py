from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class PayoutSources:
    """
    Where a store's payout wallet of each family comes from: the store's own (STORE) or the account's (ACCOUNT); None when
    the store has none.
    """

    STORE: ClassVar[str] = "store"
    ACCOUNT: ClassVar[str] = "account"

    evm: str | None
    tron: str | None

    @classmethod
    def from_fields(cls, f: Fields) -> PayoutSources:
        return cls(f.nullable_string("evm"), f.nullable_string("tron"))

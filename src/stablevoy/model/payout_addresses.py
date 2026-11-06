from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class PayoutAddresses:
    """
    The account's payout wallets per network family, None when not set. Read only: they change in the dashboard with a
    wallet signature.
    """

    evm: str | None
    tron: str | None

    @classmethod
    def from_fields(cls, f: Fields) -> PayoutAddresses:
        return cls(f.nullable_string("evm"), f.nullable_string("tron"))

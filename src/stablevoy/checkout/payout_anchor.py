from __future__ import annotations

import re

_EVM = re.compile(r"0x[0-9a-fA-F]{40}")
_TRON = re.compile(r"T[1-9A-HJ-NP-Za-km-z]{33}")


class PayoutAnchor:
    """The payout wallets your shop confirmed, put in the payment link after # so the Stablevoy payment page refuses any
    other wallet, even one a compromised server would name. Store it when the merchant confirms the wallets in your shop,
    never take it from an API answer: that answer is what it guards against."""

    def __init__(self, *, evm: str | None = None, tron: str | None = None) -> None:
        if evm is None and tron is None:
            raise ValueError("A payout anchor names at least one wallet (evm or tron)")
        if evm is not None and _EVM.fullmatch(evm) is None:
            raise ValueError("The EVM payout wallet must be an address like 0x followed by 40 hex characters")
        if tron is not None and _TRON.fullmatch(tron) is None:
            raise ValueError("The Tron payout wallet must be a Base58 address starting with T")
        self._evm = evm
        self._tron = tron

    @property
    def evm(self) -> str | None:
        return self._evm

    @property
    def tron(self) -> str | None:
        return self._tron

    def fragment(self) -> str:
        """The part after # of the payment link: payout=evm:0x...;tron:T..."""
        parts = []
        if self._evm is not None:
            parts.append(f"evm:{self._evm}")
        if self._tron is not None:
            parts.append(f"tron:{self._tron}")
        return "payout=" + ";".join(parts)

    def accepts(self, payout_address: str) -> bool:
        """Whether a payout address of an invoice is the anchored wallet of its family: EVM compared without regard to
        letter case, Tron exactly. An address of no known form matches nothing."""
        if _EVM.fullmatch(payout_address) is not None:
            return self._evm is not None and self._evm.lower() == payout_address.lower()
        if _TRON.fullmatch(payout_address) is not None:
            return self._tron == payout_address
        return False

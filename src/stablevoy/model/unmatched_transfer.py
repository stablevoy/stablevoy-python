from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class UnmatchedTransfer:
    """
    A payment to the payout wallet on a direct network (Tron) that matched no invoice, usually an exchange that took its
    withdrawal fee out of the amount. Attach it to an invoice in the Stablevoy dashboard; an API key cannot.
    """

    id: str
    network: str
    """Network key, for example tron."""
    network_name: str
    payout_address: str
    """The payout wallet the transfer arrived at."""
    from_address: str
    tx_hash: str
    token_symbol: str
    amount_usd_micros: str
    """What arrived, in millionths of a dollar, as a string: "98500137" is $98.500137."""
    detected_at: datetime
    explorer_tx_url: str
    """Prefix of the transaction page on the block explorer; Tronscan takes the hash without its 0x prefix."""
    shared_with_stores: int
    """
    How many active stores of the account offer this network. The payout wallet belongs to the account, not to one
    store, so 1 means the transfer is certainly this store's and more means it may belong to any of that many stores.
    """

    @classmethod
    def from_fields(cls, f: Fields) -> UnmatchedTransfer:
        return cls(
            f.string("id"),
            f.string("network"),
            f.string("networkName"),
            f.string("payoutAddress"),
            f.string("fromAddress"),
            f.string("txHash"),
            f.string("tokenSymbol"),
            f.string("amountUsdMicros"),
            f.date("detectedAt"),
            f.string("explorerTxUrl"),
            f.integer("sharedWithStores"),
        )

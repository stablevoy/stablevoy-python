from typing import Final


class CheckoutStep:
    """
    The steps of the payment page funnel and trail. Responses carry them as plain strings, so a step added to the API
    later reaches you as its name instead of breaking this library; compare with these constants.
    """

    CREATED: Final = "created"
    """The invoice was created (trail only)."""
    OPENED: Final = "opened"
    """The buyer opened the payment page or the widget."""
    OPTION_CHANGED: Final = "option_changed"
    """The buyer picked another network or token."""
    DETAILS_COPIED: Final = "details_copied"
    """The buyer copied the amount or the address."""
    WALLET_STARTED: Final = "wallet_started"
    WALLET_REJECTED: Final = "wallet_rejected"
    """The buyer cancelled the payment in the wallet."""
    WALLET_FAILED: Final = "wallet_failed"
    TX_SENT: Final = "tx_sent"
    """The wallet sent the transaction."""
    DETECTED: Final = "detected"
    """The first payment was seen on chain (trail only)."""
    PAID: Final = "paid"
    EXPIRED: Final = "expired"
    CANCELLED: Final = "cancelled"

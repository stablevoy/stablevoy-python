from __future__ import annotations

from stablevoy.errors.problem_issue import ProblemIssue
from stablevoy.errors.stablevoy_error import StablevoyError


class ApiError(StablevoyError):
    """
    The API answered with an error: an RFC 7807 problem document with a stable code, a readable detail and a link to the
    code's entry in the error catalog (https://stablevoy.com/docs/api/errors/).
    """

    PAYOUT_ADDRESS_NOT_SET = "payout_address_not_set"
    """No enabled network of the store has a payout wallet; Store.can_accept_payments() tells it in advance."""

    PAYOUT_ADDRESS_UNACKNOWLEDGED = "payout_address_unacknowledged"
    """
    The EVM payout wallet is not confirmed in the dashboard (or changed since) and the store has no other network to
    offer; Store.evm_payout_needs_review() and Store.can_accept_payments() tell it in advance.
    """

    INVOICE_NOT_CANCELLABLE = "invoice_not_cancellable"
    """invoices.cancel() on an invoice that already has a payment seen on chain, or is paid, expired, underpaid or on hold."""

    INVALID_INVOICE_LIFETIME = "invalid_invoice_lifetime"
    """expires_in_minutes is outside the bounds platform.limits() gives (15 to 10080 minutes)."""

    def __init__(
        self,
        *,
        status: int,
        code: str,
        detail: str,
        type: str | None,
        issues: tuple[ProblemIssue, ...],
        retry_after_seconds: int | None,
        limit_usd_cents: int | None = None,
    ) -> None:
        super().__init__(f"{detail} (HTTP {status}, {code})")
        self.status = status
        self.code = code
        self.detail = detail
        self.type = type
        self.issues = issues
        self.retry_after_seconds = retry_after_seconds
        self.limit_usd_cents = limit_usd_cents
        """For an amount refused by a limit (amount_below_minimum, amount_above_store_limit, ...): that limit in US cents."""

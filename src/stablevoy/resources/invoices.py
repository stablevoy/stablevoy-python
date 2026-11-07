from __future__ import annotations

import re
from collections.abc import Iterator

from stablevoy.http.transport import Transport
from stablevoy.model.created_invoice import CreatedInvoice
from stablevoy.model.fields import Fields
from stablevoy.model.invoice import Invoice
from stablevoy.model.invoice_page import InvoicePage
from stablevoy.model.invoice_summary import InvoiceSummary
from stablevoy.model.summary_period import SummaryPeriod

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_IDEMPOTENCY_KEY = re.compile(r"[\x21-\x7e]{1,255}")


class Invoices:
    """Invoices of the store the API key belongs to."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self,
        amount_usd_cents: int,
        *,
        external_reference: str | None = None,
        return_url: str | None = None,
        expires_in_minutes: int | None = None,
        idempotency_key: str | None = None,
    ) -> CreatedInvoice:
        """
        Creates an invoice. Pass your order id as the idempotency key: a retry with the same key and request returns the
        first invoice (replayed: True) instead of a second one, and only then does this library retry on its own.

        expires_in_minutes: how long the buyer has to pay, 15 to 10080 minutes (7 days). None: the store's payment
        window, else the platform default (platform.limits() tells it). Use a day or more for an invoice sent by email.
        """
        if not isinstance(amount_usd_cents, int) or isinstance(amount_usd_cents, bool) or amount_usd_cents < 1:
            raise ValueError("amount_usd_cents must be a positive whole number of US cents, for example 1999 for $19.99")
        # What the API accepts; anything else would be refused there, or fail inside http.client on the header.
        if idempotency_key is not None and not _IDEMPOTENCY_KEY.fullmatch(idempotency_key):
            raise ValueError("The idempotency key must be 1 to 255 printable ASCII characters without spaces, such as your order id")
        # The bounds (platform.limits()) are checked by the API, which answers invalid_invoice_lifetime.
        if expires_in_minutes is not None and (not isinstance(expires_in_minutes, int) or isinstance(expires_in_minutes, bool)):
            raise ValueError("expires_in_minutes must be a whole number of minutes, for example 60 or 1440")
        body: dict[str, object] = {"amountUsdCents": amount_usd_cents}
        if external_reference is not None:
            body["externalReference"] = external_reference
        if return_url is not None:
            body["returnUrl"] = return_url
        if expires_in_minutes is not None:
            body["expiresInMinutes"] = expires_in_minutes
        return CreatedInvoice.from_fields(Fields.of(self._transport.post("/v1/invoices", body, idempotency_key), "invoice"))

    def get(self, invoice_id: str) -> Invoice:
        _check_id(invoice_id)
        return Invoice.from_fields(Fields.of(self._transport.get(f"/v1/invoices/{invoice_id}"), "invoice"))

    def cancel(self, invoice_id: str) -> Invoice:
        """
        Cancels an invoice that is still waiting for its first payment, for example when the order was cancelled: the
        payment page tells the buyer not to pay and the webhook invoice.cancelled is sent. Cancelling it again returns it
        unchanged. Once a payment has been seen the API refuses with ApiError.INVOICE_NOT_CANCELLABLE; money that still
        arrives after a cancel makes the invoice paid_late. Not retried on its own; calling it again is safe.
        """
        _check_id(invoice_id)
        return Invoice.from_fields(Fields.of(self._transport.post(f"/v1/invoices/{invoice_id}/cancel", {}), "invoice"))

    def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        status: str | None = None,
        source: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        search: str | None = None,
    ) -> InvoicePage:
        """
        One page of invoices, newest first. Every filter is optional and they combine: ``status`` (InvoiceStatus),
        ``source`` (payment_link, woocommerce, edd, whmcs, api_key or not_recorded), ``created_from`` and ``created_to``
        (UTC days as YYYY-MM-DD, both ends included) and ``search`` (an invoice id or the start of the external reference).
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be a whole number from 1 to 100")
        for name, day in (("created_from", created_from), ("created_to", created_to)):
            if day is not None and not _DAY.fullmatch(day):
                raise ValueError(f"{name} must be a date as YYYY-MM-DD")
        # The API counts UTF-16 units, as JavaScript does: a character outside the basic plane (an emoji) is two.
        if search is not None and not 1 <= len(search.encode("utf-16-le")) // 2 <= 200:
            raise ValueError("search must be 1 to 200 characters")
        query: dict[str, str | int] = {"limit": limit}
        if cursor is not None:
            query["cursor"] = cursor
        for key, value in (("status", status), ("source", source), ("createdFrom", created_from), ("createdTo", created_to), ("q", search)):
            if value is not None:
                query[key] = value
        return InvoicePage.from_fields(Fields.of(self._transport.get("/v1/invoices", query), "invoices"))

    def summary(self, *, period: str | None = None, created_from: str | None = None, created_to: str | None = None) -> InvoiceSummary:
        """
        Totals of the invoices created in a range of UTC days: counts per status, the invoiced amount and the money
        received, also per network and token. Pass a period (SummaryPeriod) or both days as YYYY-MM-DD:
        ``summary(period=SummaryPeriod.LAST_7_DAYS)`` or ``summary(created_from="2026-10-01", created_to="2026-10-31")``.
        One request covers at most 92 days, so ask for a year in four parts; a longer range is refused with
        ApiError.INVALID_INVOICE_FILTER. The API allows 30 calls a minute per store.
        """
        has_days = created_from is not None or created_to is not None
        if (period is not None) == has_days:
            raise ValueError("Pass either period or both created_from and created_to")
        query: dict[str, str | int] = {}
        if period is not None:
            if period not in SummaryPeriod.ALL:
                raise ValueError(f"period must be one of {', '.join(SummaryPeriod.ALL)}")
            query["period"] = period
        else:
            for name, key, day in (("created_from", "createdFrom", created_from), ("created_to", "createdTo", created_to)):
                if day is None or not _DAY.fullmatch(day):
                    raise ValueError(f"{name} must be a date as YYYY-MM-DD")
                query[key] = day
        return InvoiceSummary.from_fields(Fields.of(self._transport.get("/v1/invoices/summary", query), "summary"))

    def all(
        self,
        *,
        status: str | None = None,
        page_size: int = 100,
        source: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        search: str | None = None,
    ) -> Iterator[Invoice]:
        """Every invoice, newest first, fetching the pages as you iterate; the filters are those of ``list()``."""
        cursor: str | None = None
        while True:
            page = self.list(
                limit=page_size,
                cursor=cursor,
                status=status,
                source=source,
                created_from=created_from,
                created_to=created_to,
                search=search,
            )
            yield from page.items
            if page.next_cursor is None:
                return
            cursor = page.next_cursor


def _check_id(invoice_id: str) -> None:
    # Ids are UUIDs; anything else (such as "..") could make the request reach another path with your key.
    if not _UUID.fullmatch(invoice_id):
        raise ValueError("An invoice id is a UUID, like 7c3360b5-e8cc-4775-8a13-7324d4f1296e")

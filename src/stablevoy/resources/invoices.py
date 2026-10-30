from __future__ import annotations

import re
from collections.abc import Iterator

from stablevoy.http.transport import Transport
from stablevoy.model.created_invoice import CreatedInvoice
from stablevoy.model.fields import Fields
from stablevoy.model.invoice import Invoice
from stablevoy.model.invoice_page import InvoicePage

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


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
        idempotency_key: str | None = None,
    ) -> CreatedInvoice:
        """
        Creates an invoice. Pass your order id as the idempotency key: a retry with the same key and request returns the
        first invoice (replayed: True) instead of a second one, and only then does this library retry on its own.
        """
        if not isinstance(amount_usd_cents, int) or isinstance(amount_usd_cents, bool) or amount_usd_cents < 1:
            raise ValueError("amount_usd_cents must be a positive whole number of US cents, for example 1999 for $19.99")
        body: dict[str, object] = {"amountUsdCents": amount_usd_cents}
        if external_reference is not None:
            body["externalReference"] = external_reference
        if return_url is not None:
            body["returnUrl"] = return_url
        return CreatedInvoice.from_fields(Fields.of(self._transport.post("/v1/invoices", body, idempotency_key), "invoice"))

    def get(self, invoice_id: str) -> Invoice:
        # Ids are UUIDs; anything else (such as "..") could make the request reach another path with your key.
        if not _UUID.fullmatch(invoice_id):
            raise ValueError("An invoice id is a UUID, like 7c3360b5-e8cc-4775-8a13-7324d4f1296e")
        return Invoice.from_fields(Fields.of(self._transport.get(f"/v1/invoices/{invoice_id}"), "invoice"))

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
        if not 1 <= limit <= 100:
            raise ValueError("limit must be from 1 to 100")
        for name, day in (("created_from", created_from), ("created_to", created_to)):
            if day is not None and not _DAY.fullmatch(day):
                raise ValueError(f"{name} must be a date as YYYY-MM-DD")
        if search is not None and not 1 <= len(search) <= 200:
            raise ValueError("search must be 1 to 200 characters")
        query: dict[str, str | int] = {"limit": limit}
        if cursor is not None:
            query["cursor"] = cursor
        for key, value in (("status", status), ("source", source), ("createdFrom", created_from), ("createdTo", created_to), ("q", search)):
            if value is not None:
                query[key] = value
        return InvoicePage.from_fields(Fields.of(self._transport.get("/v1/invoices", query), "invoices"))

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

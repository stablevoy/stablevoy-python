from __future__ import annotations

from dataclasses import dataclass

from stablevoy.model.fields import Fields
from stablevoy.model.invoice import Invoice


@dataclass(frozen=True)
class InvoicePage:
    """One page of invoices, newest first; pass next_cursor to get the next page, None on the last one."""

    items: tuple[Invoice, ...]
    next_cursor: str | None

    @classmethod
    def from_fields(cls, f: Fields) -> InvoicePage:
        return cls(f.objects("items", Invoice.from_fields), f.nullable_string("nextCursor"))

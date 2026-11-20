import re

from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.http.transport import Transport
from stablevoy.model.currency import Currency
from stablevoy.model.fields import Fields

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


class Currencies:
    """Currencies an invoice can be priced in, and their exchange rates. Read only: a store's own rate is set in the dashboard."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(self) -> tuple[Currency, ...]:
        """Every supported currency with the market rate in use (ECB reference rates, checked against Coinbase)."""
        return _parse(self._transport.get("/v1/currencies"))

    def for_store(self, store_id: str) -> tuple[Currency, ...]:
        """
        The same list for one store (the key's own store), with its own fixed rates and the rate an invoice of the store
        would use now. effective None: an invoice in that currency is refused right now.
        """
        # Ids are UUIDs; anything else (such as "..") could make the request reach another path with your key.
        if not _UUID.fullmatch(store_id):
            raise ValueError("A store id is a UUID, like 7c3360b5-e8cc-4775-8a13-7324d4f1296e")
        return _parse(self._transport.get(f"/v1/stores/{store_id}/currencies"))


def _parse(data: object) -> tuple[Currency, ...]:
    if not isinstance(data, list):
        raise UnexpectedResponseError("currencies is not a list")
    return tuple(Currency.from_fields(Fields.of(item, f"currencies[{i}]")) for i, item in enumerate(data))

from stablevoy.http.transport import Transport
from stablevoy.model.checkout_funnel import CheckoutFunnel
from stablevoy.model.fields import Fields
from stablevoy.model.store import Store
from stablevoy.model.summary_range import summary_range_query


class Stores:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def current(self) -> Store:
        """The store the API key belongs to: a cheap way to check that the key works."""
        return Store.from_fields(Fields.of(self._transport.get("/v1/store"), "store"))

    def checkout_funnel(
        self, *, period: str | None = None, created_from: str | None = None, created_to: str | None = None
    ) -> CheckoutFunnel:
        """
        Where buyers stop on the payment page, for the store's invoices created in a range of UTC days: how many opened
        the page, changed the network or token, copied the payment details, started a wallet, had it refused or failed,
        sent the transaction, saw a payment and were paid. The same range as invoices.summary(): a period (SummaryPeriod)
        or both days, at most 92 days. Counts of invoices, not of visits. The API allows 30 calls a minute per store.
        """
        query = summary_range_query(period, created_from, created_to)
        return CheckoutFunnel.from_fields(Fields.of(self._transport.get("/v1/store/checkout-funnel", query), "checkoutFunnel"))

    def revoke_current_key(self) -> None:
        """
        Revokes the API key of this client; it stops working at once (use it when the shop disconnects). A key that is
        already revoked answers with AuthenticationError, which for a disconnect means the same.
        """
        self._transport.delete("/v1/store/api-keys/current")

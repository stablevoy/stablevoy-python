from stablevoy.http.transport import Transport
from stablevoy.model.fields import Fields
from stablevoy.model.store import Store


class Stores:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def current(self) -> Store:
        """The store the API key belongs to: a cheap way to check that the key works."""
        return Store.from_fields(Fields.of(self._transport.get("/v1/store"), "store"))

    def revoke_current_key(self) -> None:
        """
        Revokes the API key of this client; it stops working at once (use it when the shop disconnects). A key that is
        already revoked answers with AuthenticationError, which for a disconnect means the same.
        """
        self._transport.delete("/v1/store/api-keys/current")

from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.http.transport import Transport
from stablevoy.model.fields import Fields
from stablevoy.model.unmatched_transfer import UnmatchedTransfer


class UnmatchedTransfers:
    """Transfers to the payout wallet that matched no invoice, on the networks of the key's store. Read only."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(self) -> tuple[UnmatchedTransfer, ...]:
        """Newest first, at most 100. The API allows 30 calls a minute per store."""
        data = self._transport.get("/v1/unmatched-transfers")
        if not isinstance(data, list):
            raise UnexpectedResponseError("unmatchedTransfers is not a list")
        return tuple(UnmatchedTransfer.from_fields(Fields.of(item, f"unmatchedTransfers[{i}]")) for i, item in enumerate(data))

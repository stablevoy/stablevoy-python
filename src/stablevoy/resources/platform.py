from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.http.transport import Transport
from stablevoy.model.fields import Fields
from stablevoy.model.limits import Limits
from stablevoy.model.network import Network
from stablevoy.model.pricing import Pricing


class Platform:
    """Public facts about the platform: invoice limits, the price list and the supported networks."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def limits(self) -> Limits:
        return Limits.from_fields(Fields.of(self._transport.get("/v1/limits"), "limits"))

    def pricing(self) -> Pricing:
        return Pricing.from_fields(Fields.of(self._transport.get("/v1/pricing"), "pricing"))

    def networks(self) -> tuple[Network, ...]:
        data = self._transport.get("/v1/networks")
        if not isinstance(data, list):
            raise UnexpectedResponseError("networks is not a list")
        return tuple(Network.from_fields(Fields.of(item, f"networks[{i}]")) for i, item in enumerate(data))

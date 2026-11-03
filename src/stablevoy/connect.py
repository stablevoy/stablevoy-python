from __future__ import annotations

import time
from collections.abc import Callable

from stablevoy.http.create_urllib_transport import create_urllib_transport
from stablevoy.http.opener import Opener
from stablevoy.http.retry_policy import RetryPolicy
from stablevoy.http.transport import Transport
from stablevoy.model.connected_store import ConnectedStore
from stablevoy.model.fields import Fields


class StablevoyConnect:
    """
    One-click connect: the shop sends the merchant to the Stablevoy dashboard with a PKCE challenge, gets a code back on its
    callback and redeems it here for its API key and webhook secret. Needs no API key, since the shop has none yet.
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @classmethod
    def create(
        cls,
        *,
        base_url: str = "https://api.stablevoy.com",
        retries: RetryPolicy | None = None,
        timeout_seconds: float = 30.0,
        user_agent_suffix: str | None = None,
        opener: Opener | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> StablevoyConnect:
        return cls(
            create_urllib_transport(
                None,
                base_url=base_url,
                retries=retries,
                timeout_seconds=timeout_seconds,
                user_agent_suffix=user_agent_suffix,
                opener=opener,
                sleep=sleep,
            )
        )

    def exchange(self, *, code: str, code_verifier: str, site: str) -> ConnectedStore:
        """
        Redeems the code. It works once, so this call is never retried: after a lost answer the merchant clicks Connect
        again. A refusal (invalid_connect_code, store_linked_to_other_site, store_connected_other_platform) is an ApiError
        with that code. ``site`` is the shop's own URL, the same one sent when the connection was started.
        """
        body = {"code": code, "codeVerifier": code_verifier, "site": site}
        return ConnectedStore.from_fields(Fields.of(self._transport.post("/v1/connect/exchange", body), "connected"))

from __future__ import annotations

import time
from collections.abc import Callable

from stablevoy.http.create_urllib_transport import create_urllib_transport
from stablevoy.http.opener import Opener
from stablevoy.http.retry_policy import RetryPolicy
from stablevoy.http.transport import Transport
from stablevoy.resources.invoices import Invoices
from stablevoy.resources.platform import Platform
from stablevoy.resources.stores import Stores


class Stablevoy:
    """The Stablevoy API: ``stablevoy = Stablevoy.create(os.environ["STABLEVOY_API_KEY"])``."""

    def __init__(self, invoices: Invoices, stores: Stores, platform: Platform) -> None:
        self.invoices = invoices
        self.stores = stores
        self.platform = platform

    @classmethod
    def create(
        cls,
        api_key: str,
        *,
        base_url: str = "https://api.stablevoy.com",
        retries: RetryPolicy | None = None,
        timeout_seconds: float = 30.0,
        user_agent_suffix: str | None = None,
        opener: Opener | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> Stablevoy:
        return cls.from_transport(
            create_urllib_transport(
                api_key,
                base_url=base_url,
                retries=retries,
                timeout_seconds=timeout_seconds,
                user_agent_suffix=user_agent_suffix,
                opener=opener,
                sleep=sleep,
            )
        )

    @classmethod
    def from_transport(cls, transport: Transport) -> Stablevoy:
        return cls(Invoices(transport), Stores(transport), Platform(transport))

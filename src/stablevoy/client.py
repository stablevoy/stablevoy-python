from __future__ import annotations

import platform
import time
from collections.abc import Callable

from stablevoy._version import __version__
from stablevoy.http.error_factory import ErrorFactory
from stablevoy.http.opener import Opener
from stablevoy.http.retry_policy import RetryPolicy
from stablevoy.http.transport import Transport
from stablevoy.http.urllib_opener import UrllibOpener
from stablevoy.http.urllib_transport import UrllibTransport
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
        user_agent = f"stablevoy-python/{__version__} Python/{platform.python_version()}"
        if user_agent_suffix is not None:
            user_agent += f" {user_agent_suffix}"
        return cls.from_transport(
            UrllibTransport(
                api_key=api_key,
                base_url=base_url,
                user_agent=user_agent,
                retries=retries if retries is not None else RetryPolicy(),
                opener=opener if opener is not None else UrllibOpener(),
                sleep=sleep,
                errors=ErrorFactory(),
                timeout_seconds=timeout_seconds,
            )
        )

    @classmethod
    def from_transport(cls, transport: Transport) -> Stablevoy:
        return cls(Invoices(transport), Stores(transport), Platform(transport))

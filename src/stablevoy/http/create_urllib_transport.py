from __future__ import annotations

import platform
from collections.abc import Callable

from stablevoy._version import __version__
from stablevoy.http.error_factory import ErrorFactory
from stablevoy.http.opener import Opener
from stablevoy.http.retry_policy import RetryPolicy
from stablevoy.http.urllib_opener import UrllibOpener
from stablevoy.http.urllib_transport import UrllibTransport


def create_urllib_transport(
    api_key: str | None,
    *,
    base_url: str,
    retries: RetryPolicy | None,
    timeout_seconds: float,
    user_agent_suffix: str | None,
    opener: Opener | None,
    sleep: Callable[[float], None],
) -> UrllibTransport:
    """The transport Stablevoy and StablevoyConnect talk through, built the same way for both."""
    user_agent = f"stablevoy-python/{__version__} Python/{platform.python_version()}"
    if user_agent_suffix is not None:
        user_agent += f" {user_agent_suffix}"
    return UrllibTransport(
        api_key=api_key,
        base_url=base_url,
        user_agent=user_agent,
        retries=retries if retries is not None else RetryPolicy(),
        opener=opener if opener is not None else UrllibOpener(),
        sleep=sleep,
        errors=ErrorFactory(),
        timeout_seconds=timeout_seconds,
    )

from collections.abc import Mapping
from typing import Protocol


class Transport(Protocol):
    """Sends one API call and returns the decoded JSON answer, or raises the matching error. The resources depend on it only."""

    def get(self, path: str, query: Mapping[str, str | int] | None = None) -> object: ...

    def post(self, path: str, body: Mapping[str, object], idempotency_key: str | None = None) -> object: ...

    def delete(self, path: str) -> None:
        """A call that answers 204 without a body. Deleting twice does no harm, so it is retried like a read."""
        ...

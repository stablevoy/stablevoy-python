from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from stablevoy.model.fields import Fields


@dataclass(frozen=True)
class WebhookHealth:
    """
    State of the store's webhook endpoint. FAILING: at least 10 failed attempts and not paused yet, fix the endpoint
    before pauses_at. PAUSED: it failed for 24 hours with at least 10 failed attempts; new events wait (up to 30 days)
    until the merchant resumes it in the dashboard. Faults of Stablevoy's own delivery service never count against it.
    """

    ACTIVE: ClassVar[str] = "active"
    FAILING: ClassVar[str] = "failing"
    PAUSED: ClassVar[str] = "paused"

    status: str
    """ACTIVE, FAILING or PAUSED."""
    failing_since: datetime | None
    """First failed delivery since the last successful one; None while deliveries succeed."""
    failed_attempts: int
    """Failed deliveries since failing_since."""
    pauses_at: datetime | None
    """While it fails and is not paused: the earliest moment it is paused if it keeps failing; None otherwise."""
    paused_at: datetime | None
    pause_reason: str | None
    """The last error when it was paused."""

    @classmethod
    def from_fields(cls, f: Fields) -> WebhookHealth:
        return cls(
            f.string("status"),
            f.nullable_date("failingSince"),
            f.integer("failedAttempts"),
            f.nullable_date("pausesAt"),
            f.nullable_date("pausedAt"),
            f.nullable_string("pauseReason"),
        )

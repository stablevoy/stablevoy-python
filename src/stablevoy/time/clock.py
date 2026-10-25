from typing import Protocol


class Clock(Protocol):
    def now(self) -> int:
        """Seconds since the Unix epoch."""
        ...

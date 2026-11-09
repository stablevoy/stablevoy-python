from __future__ import annotations

from enum import StrEnum


class KeyCheck(StrEnum):
    """How a pasted or received key or secret looks."""

    OK = "ok"
    MISTYPED = "mistyped"
    """A new-format key or secret whose checksum does not match: a character is wrong or missing."""
    NOT_A_KEY = "not_a_key"

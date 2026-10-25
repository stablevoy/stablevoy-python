from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

from stablevoy.errors.unexpected_response_error import UnexpectedResponseError

T = TypeVar("T")


class Fields:
    """Strict reads from a decoded JSON object. A missing field or one of the wrong type is an error naming it, never a silent default."""

    def __init__(self, data: dict[str, object], path: str) -> None:
        self._data = data
        self._path = path

    @classmethod
    def of(cls, value: object, path: str) -> Fields:
        if not isinstance(value, dict):
            raise UnexpectedResponseError(f"{path} is not a JSON object")
        return cls(value, path)

    def string(self, key: str) -> str:
        value = self._value(key)
        if not isinstance(value, str):
            raise self._wrong(key, "a string")
        return value

    def nullable_string(self, key: str) -> str | None:
        value = self._value(key)
        if value is not None and not isinstance(value, str):
            raise self._wrong(key, "a string or null")
        return value

    def integer(self, key: str) -> int:
        value = self._value(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise self._wrong(key, "an integer")
        return value

    def nullable_integer(self, key: str) -> int | None:
        value = self._value(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise self._wrong(key, "an integer or null")
        return value

    def boolean(self, key: str) -> bool:
        value = self._value(key)
        if not isinstance(value, bool):
            raise self._wrong(key, "a boolean")
        return value

    def date(self, key: str) -> datetime:
        return self._parse_date(key, self.string(key))

    def nullable_date(self, key: str) -> datetime | None:
        value = self.nullable_string(key)
        return None if value is None else self._parse_date(key, value)

    def strings(self, key: str) -> tuple[str, ...]:
        items = self.values(key)
        if not all(isinstance(item, str) for item in items):
            raise self._wrong(key, "a list of strings")
        return tuple(str(item) for item in items)

    def values(self, key: str) -> list[object]:
        value = self._value(key)
        if not isinstance(value, list):
            raise self._wrong(key, "a list")
        return value

    def objects(self, key: str, parse: Callable[[Fields], T]) -> tuple[T, ...]:
        """Each item of a list of objects, parsed with ``parse``."""
        return tuple(parse(Fields.of(item, f"{self._path}.{key}[{i}]")) for i, item in enumerate(self.values(key)))

    def child(self, key: str) -> Fields:
        return Fields.of(self._value(key), f"{self._path}.{key}")

    def raw(self) -> dict[str, object]:
        """The object as decoded, for data this library does not model."""
        return self._data

    def _value(self, key: str) -> object:
        if key not in self._data:
            raise UnexpectedResponseError(f"{self._path}.{key} is missing")
        return self._data[key]

    def _parse_date(self, key: str, value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            raise self._wrong(key, "an ISO 8601 date") from None
        if parsed.tzinfo is None:
            raise self._wrong(key, "an ISO 8601 date with a time zone")
        return parsed

    def _wrong(self, key: str, expected: str) -> UnexpectedResponseError:
        return UnexpectedResponseError(f"{self._path}.{key} is not {expected}")

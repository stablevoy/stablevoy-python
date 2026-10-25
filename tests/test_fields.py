from __future__ import annotations

from collections.abc import Callable

import pytest

from stablevoy import UnexpectedResponseError
from stablevoy.model.fields import Fields


@pytest.mark.parametrize(
    ("data", "read", "message"),
    [
        ({"a": 1}, lambda f: f.string("b"), "x.b is missing"),
        ({"a": 1}, lambda f: f.string("a"), "x.a is not a string"),
        ({"a": 1}, lambda f: f.nullable_string("a"), "x.a is not a string or null"),
        ({"a": "1"}, lambda f: f.integer("a"), "x.a is not an integer"),
        ({"a": True}, lambda f: f.integer("a"), "x.a is not an integer"),
        ({"a": 1.5}, lambda f: f.nullable_integer("a"), "x.a is not an integer or null"),
        ({"a": False}, lambda f: f.nullable_integer("a"), "x.a is not an integer or null"),
        ({"a": 1}, lambda f: f.boolean("a"), "x.a is not a boolean"),
        ({"a": "yesterday-ish"}, lambda f: f.date("a"), "x.a is not an ISO 8601 date"),
        ({"a": "2026-10-25T10:00:00"}, lambda f: f.date("a"), "x.a is not an ISO 8601 date with a time zone"),
        ({"a": {"k": 1}}, lambda f: f.values("a"), "x.a is not a list"),
        ({"a": [1]}, lambda f: f.strings("a"), "x.a is not a list of strings"),
        ({"a": [1, 2]}, lambda f: f.child("a"), "x.a is not a JSON object"),
    ],
)
def test_names_the_field_that_is_missing_or_wrong(data: dict[str, object], read: Callable[[Fields], object], message: str) -> None:
    with pytest.raises(UnexpectedResponseError, match=message.replace(".", "\\.")):
        read(Fields(data, "x"))


def test_reads_nulls_and_dates() -> None:
    f = Fields({"s": None, "i": None, "d": None, "e": "2026-10-25T10:00:00.000Z"}, "x")
    assert (f.nullable_string("s"), f.nullable_integer("i"), f.nullable_date("d")) == (None, None, None)
    assert f.nullable_date("e") is not None


@pytest.mark.parametrize("value", [[1, 2], None, "text"])
def test_refuses_what_is_no_object(value: object) -> None:
    with pytest.raises(UnexpectedResponseError):
        Fields.of(value, "x")

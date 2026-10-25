from __future__ import annotations

import re

import pytest

from stablevoy import (
    ApiError,
    AuthenticationError,
    MaintenanceError,
    NotFoundError,
    ProblemIssue,
    RateLimitedError,
    RetryPolicy,
    StablevoyError,
    TransportError,
    UnexpectedResponseError,
    ValidationError,
)

from .support import INVOICE_ID, answer, client, example, problem


@pytest.mark.parametrize(
    ("status", "code", "error_type"),
    [
        (401, "authentication_failed", AuthenticationError),
        (404, "not_found", NotFoundError),
        (400, "validation_failed", ValidationError),
        (422, "amount_below_minimum", ValidationError),
        (409, "conflict", ApiError),
        (503, "networks_unavailable", ApiError),
    ],
)
def test_maps_each_problem_to_its_error(status: int, code: str, error_type: type[ApiError]) -> None:
    t = client(answer(status, problem(status, code, "Something went wrong")), retries=RetryPolicy.none())
    with pytest.raises(StablevoyError) as caught:
        t.client.invoices.get(INVOICE_ID)
    error = caught.value
    assert type(error) is error_type
    assert isinstance(error, ApiError)
    assert (error.status, error.code, error.detail) == (status, code, "Something went wrong")
    assert error.type == f"https://stablevoy.com/docs/api/errors/#error-{code}"
    assert f"HTTP {status}" in str(error)


def test_keeps_the_issues_of_a_validation_error_and_drops_malformed_ones() -> None:
    body = {
        **problem(400, "validation_failed", "Invalid body"),
        "issues": [{"path": "amountUsdCents", "message": "Expected integer"}, "junk", {"path": 1}],
    }
    with pytest.raises(ValidationError) as caught:
        client(answer(400, body)).client.invoices.create(1)
    assert caught.value.issues == (ProblemIssue("amountUsdCents", "Expected integer"),)


@pytest.mark.parametrize("body", ["Bad Gateway", "[1]", '{"issues":"none"}'])
def test_names_an_error_without_a_usable_problem_body_by_its_status(body: str) -> None:
    with pytest.raises(ApiError) as caught:
        client(answer(502, body), retries=RetryPolicy.none()).client.stores.current()
    assert (caught.value.code, caught.value.detail, caught.value.type, caught.value.issues) == (
        "http_502",
        "The API answered HTTP 502",
        None,
        (),
    )


def test_retries_a_read_on_rate_limit_as_long_as_retry_after_says() -> None:
    t = client(answer(429, problem(429, "rate_limited", "Slow down"), {"Retry-After": "3"}), answer(200, example("GET", "/v1/limits", 200)))
    t.client.platform.limits()
    assert t.slept == [3]
    assert len(t.opener.sent) == 2


def test_backs_off_without_a_readable_retry_after_and_gives_up_after_the_last_retry() -> None:
    def limited() -> object:
        return answer(429, problem(429, "rate_limited", "Slow down"), {"Retry-After": "soon"})

    t = client(limited(), limited(), limited())  # type: ignore[arg-type]
    with pytest.raises(RateLimitedError) as caught:
        t.client.platform.limits()
    assert caught.value.retry_after_seconds is None
    assert t.slept == [1, 2]


def test_does_not_sleep_through_maintenance_but_reports_when_to_come_back() -> None:
    t = client(answer(503, problem(503, "maintenance", "Stablevoy is under maintenance."), {"Retry-After": "300"}))
    with pytest.raises(MaintenanceError) as caught:
        t.client.invoices.get(INVOICE_ID)
    assert caught.value.retry_after_seconds == 300
    assert t.slept == []


def test_retries_a_create_only_with_an_idempotency_key() -> None:
    busy = answer(503, problem(503, "maintenance", "Back soon"), {"Retry-After": "2"})
    with_key = client(busy, answer(201, example("POST", "/v1/invoices", 201)))
    with_key.client.invoices.create(1999, idempotency_key="order-1")
    assert with_key.slept == [2]

    without_key = client(busy)
    with pytest.raises(MaintenanceError):
        without_key.client.invoices.create(1999)
    assert without_key.slept == []
    assert len(without_key.opener.sent) == 1


def test_does_not_retry_an_error_a_repeat_cannot_fix() -> None:
    t = client(answer(404, problem(404, "not_found", "Invoice not found")))
    with pytest.raises(NotFoundError):
        t.client.invoices.get(INVOICE_ID)
    assert t.slept == []


def test_retries_a_failed_connection_then_reports_it_with_the_cause() -> None:
    retried = client(OSError("timed out"), answer(200, example("GET", "/v1/limits", 200)))
    retried.client.platform.limits()
    assert retried.slept == [1]

    failed = client(ConnectionResetError("reset by peer"), retries=RetryPolicy.none())
    with pytest.raises(TransportError, match="Cannot reach the Stablevoy API: reset by peer") as caught:
        failed.client.platform.limits()
    assert isinstance(caught.value.__cause__, ConnectionResetError)


def test_never_retries_a_create_without_a_key_after_a_failed_connection() -> None:
    t = client(OSError("timed out"))
    with pytest.raises(TransportError):
        t.client.invoices.create(1)
    assert t.slept == []


@pytest.mark.parametrize("body", ["<html>", '"text"'])
def test_refuses_an_answer_that_is_not_a_json_object_or_list(body: str) -> None:
    with pytest.raises(UnexpectedResponseError):
        client(answer(200, body)).client.platform.limits()


def test_names_the_field_of_an_answer_it_cannot_read() -> None:
    with pytest.raises(UnexpectedResponseError, match=re.escape("limits.maxInvoiceUsdCents is not an integer")):
        client(answer(200, {"minInvoiceUsdCents": 500, "maxInvoiceUsdCents": "1000"})).client.platform.limits()


def test_refuses_negative_retry_settings() -> None:
    with pytest.raises(ValueError, match="negative"):
        RetryPolicy(-1)

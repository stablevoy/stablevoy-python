from __future__ import annotations

import json

import pytest

from stablevoy import (
    AuthenticationError,
    ConfigurationError,
    MaintenanceError,
    StablevoyConnect,
    TransportError,
    UnexpectedResponseError,
    ValidationError,
)
from stablevoy.http.http_answer import HttpAnswer

from .support import FakeOpener, answer, client, example, problem

SITE = "https://shop.example.com"


def connect(*answers: HttpAnswer | OSError) -> tuple[StablevoyConnect, FakeOpener, list[float]]:
    opener = FakeOpener(list(answers))
    slept: list[float] = []
    return StablevoyConnect.create(opener=opener, sleep=slept.append), opener, slept


def test_redeems_a_connect_code_without_an_api_key() -> None:
    example_answer = example("POST", "/v1/connect/exchange", 200)
    client_, opener, _ = connect(answer(200, example_answer))
    store = client_.exchange(code="code-1", code_verifier="verifier-1", site=SITE)
    sent = opener.last
    assert sent.method == "POST"
    assert sent.url == "https://api.stablevoy.com/v1/connect/exchange"
    assert "Authorization" not in sent.headers
    assert sent.headers["Content-type"] == "application/json"
    assert json.loads(sent.body or b"") == {"code": "code-1", "codeVerifier": "verifier-1", "site": SITE}
    expected = example_answer["store"]
    assert isinstance(expected, dict)
    assert (store.api_key, store.webhook_secret, store.store_id, store.store_name) == (
        example_answer["apiKey"],
        example_answer["webhookSecret"],
        expected["id"],
        expected["name"],
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"apiKey": "pk_live_1"}, "connected.apiKey is not an API key (svk_live_, svk_test_, or the older sk_live_, sk_test_)"),
        ({"webhookSecret": "secret"}, "connected.webhookSecret is not a webhook secret (svwhsec_, or the older whsec_)"),
        ({"store": None}, "connected.store is not a JSON object"),
        ({"store": {"id": "x"}}, "connected.store.name is missing"),
    ],
)
def test_refuses_an_answer_without_a_usable_key_secret_or_store(change: dict[str, object], message: str) -> None:
    client_, _, _ = connect(answer(200, {**example("POST", "/v1/connect/exchange", 200), **change}))
    with pytest.raises(UnexpectedResponseError, match=message.replace("(", r"\(").replace(")", r"\)")):
        client_.exchange(code="c", code_verifier="v", site=SITE)


def test_raises_the_refusal_of_the_api() -> None:
    client_, _, _ = connect(answer(400, problem(400, "invalid_connect_code", "This connection code cannot be used.")))
    with pytest.raises(ValidationError) as caught:
        client_.exchange(code="c", code_verifier="v", site=SITE)
    assert caught.value.code == "invalid_connect_code"


def test_never_repeats_an_exchange_the_first_one_spends_the_code() -> None:
    busy, opener, slept = connect(answer(503, problem(503, "maintenance", "Back soon"), {"Retry-After": "1"}))
    with pytest.raises(MaintenanceError):
        busy.exchange(code="c", code_verifier="v", site=SITE)
    assert len(opener.sent) == 1
    assert slept == []

    down, _, slept = connect(ConnectionRefusedError("refused"))
    with pytest.raises(TransportError):
        down.exchange(code="c", code_verifier="v", site=SITE)
    assert slept == []


def test_applies_the_same_base_url_check() -> None:
    with pytest.raises(ConfigurationError):
        StablevoyConnect.create(base_url="http://api.stablevoy.com")


def test_revokes_the_key_of_the_client() -> None:
    t = client(answer(204, ""))
    t.client.stores.revoke_current_key()
    assert (t.opener.last.method, t.opener.last.url) == ("DELETE", "https://api.stablevoy.com/v1/store/api-keys/current")
    assert t.opener.last.headers["Authorization"] == "Bearer sk_test_key"


def test_repeats_a_revoke_like_a_read() -> None:
    t = client(
        answer(502, "<html>Bad gateway</html>"),
        answer(503, problem(503, "maintenance", "Back soon"), {"Retry-After": "2"}),
        answer(204, ""),
    )
    t.client.stores.revoke_current_key()
    assert t.slept == [1, 2]


def test_raises_a_key_that_is_already_revoked() -> None:
    t = client(answer(401, problem(401, "authentication_failed", "Invalid API key")))
    with pytest.raises(AuthenticationError):
        t.client.stores.revoke_current_key()

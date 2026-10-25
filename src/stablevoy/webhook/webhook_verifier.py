from __future__ import annotations

import hashlib
import hmac
import json
import re

from stablevoy.errors.signature_error import SignatureError
from stablevoy.errors.unexpected_response_error import UnexpectedResponseError
from stablevoy.model.fields import Fields
from stablevoy.time.clock import Clock
from stablevoy.time.system_clock import SystemClock
from stablevoy.webhook.webhook_event import WebhookEvent


class WebhookVerifier:
    """
    Checks the X-Stablevoy-Signature header of a webhook (t=<unix>,v1=<hex hmac-sha256(secret, t + "." + raw body)>) and
    returns the event. Pass the raw request body exactly as received, before any JSON parsing.
    """

    def __init__(self, secret: str, *, tolerance_seconds: int = 300, clock: Clock | None = None) -> None:
        if not secret:
            raise ValueError("The webhook signing secret is empty. It is shown once when you set the webhook URL in the dashboard.")
        if tolerance_seconds < 1:
            raise ValueError("tolerance_seconds must be at least 1")
        self._secret = secret.encode()
        self._tolerance = tolerance_seconds
        self._clock: Clock = clock if clock is not None else SystemClock()

    def verify(self, raw_body: bytes | str, signature_header: str | None) -> WebhookEvent:
        body = raw_body.encode() if isinstance(raw_body, str) else raw_body
        timestamp, signatures = self._parse(signature_header or "")
        if abs(self._clock.now() - timestamp) > self._tolerance:
            raise SignatureError("The webhook signature is too old or from the future; check the server clock")
        expected = hmac.new(self._secret, str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, signature) for signature in signatures):
            raise SignatureError("The webhook signature does not match: wrong secret, or the body was changed")
        try:
            decoded: object = json.loads(body)
        except ValueError as error:
            raise SignatureError("The webhook is signed but its body is not JSON") from error
        try:
            return WebhookEvent.from_fields(Fields.of(decoded, "event"))
        except UnexpectedResponseError as error:
            raise SignatureError(f"The webhook is signed but its body is not a Stablevoy event: {error}") from error

    @staticmethod
    def _parse(header: str) -> tuple[int, list[str]]:
        if not header.strip():
            raise SignatureError("The X-Stablevoy-Signature header is missing")
        timestamp: int | None = None
        signatures: list[str] = []
        for part in header.split(","):
            key, _, value = part.strip().partition("=")
            if key == "t" and re.fullmatch(r"\d{1,12}", value):
                timestamp = int(value)
            elif key == "v1" and re.fullmatch(r"[0-9a-f]{1,128}", value):
                signatures.append(value)
        if timestamp is None or not signatures:
            raise SignatureError("The X-Stablevoy-Signature header is malformed")
        return timestamp, signatures

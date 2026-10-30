# Stablevoy Python SDK

[![CI](https://github.com/stablevoy/stablevoy-python/actions/workflows/ci.yml/badge.svg)](https://github.com/stablevoy/stablevoy-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/stablevoy)](https://pypi.org/project/stablevoy/)

Python client for [Stablevoy](https://stablevoy.com), the non-custodial gateway for USDT and USDC payments. Customers pay on chain and the money goes straight to your own wallet: USDC and USDT on Base, Arbitrum, Optimism, Avalanche, Polygon and BNB Chain, and USDT (TRC20) on Tron with no fee.

The library creates invoices, reads them, and verifies the signed webhooks that tell your shop an order is paid. It has no dependencies, needs Python 3.11 or newer and is fully typed.

## Install

```bash
pip install stablevoy
```

## Create an invoice and send the buyer to pay

Create an API key for your store in the [Stablevoy dashboard](https://stablevoy.com/app/).

```python
import os

from stablevoy import Stablevoy

stablevoy = Stablevoy.create(os.environ["STABLEVOY_API_KEY"])

created = stablevoy.invoices.create(
    2599,  # $25.99 in US cents
    external_reference="order-1042",  # your order id, sent back in webhooks
    return_url="https://shop.example/orders/1042",
    idempotency_key="order-1042",  # a retry returns the same invoice, never a second one
)

# Send the buyer to created.checkout_url
```

Read an invoice with `stablevoy.invoices.get(invoice_id)`, or walk them all:

```python
for invoice in stablevoy.invoices.all(status="paid"):
    print(invoice.external_reference, invoice.amount_usd_cents)
```

Narrow the list by source, created days (UTC, both ends included) or a search by invoice id or the start of your order reference. Each invoice says where it came from:

```python
from stablevoy import InvoiceSource

for invoice in stablevoy.invoices.all(source=InvoiceSource.PAYMENT_LINK, created_from="2026-11-01", created_to="2026-11-30"):
    print(invoice.id, invoice.source.kind if invoice.source else None)
```

## Verify webhooks

Stablevoy posts an event to your webhook URL when an invoice is paid, overpaid, underpaid, expired, paid late or put on hold. Check the signature before you trust it, using the signing secret shown when you set the webhook in the dashboard. Pass the raw body, exactly as received.

Flask:

```python
from flask import Flask, request

from stablevoy import SignatureError, WebhookVerifier

verifier = WebhookVerifier(os.environ["STABLEVOY_WEBHOOK_SECRET"])
app = Flask(__name__)


@app.post("/stablevoy/webhook")
def stablevoy_webhook():
    try:
        event = verifier.verify(request.get_data(), request.headers.get("X-Stablevoy-Signature"))
    except SignatureError:
        return "", 400
    if event.invoice is not None and event.invoice.is_paid():
        ...  # mark the order event.invoice.external_reference as paid; use event.id to handle each event once
    return "", 200
```

Django: `verifier.verify(request.body, request.headers.get("X-Stablevoy-Signature"))`. FastAPI: `verifier.verify(await request.body(), request.headers.get("X-Stablevoy-Signature"))`.

## Errors and retries

Every error extends `StablevoyError`. API errors are `ApiError` with the HTTP `status`, a stable `code`, a readable `detail` and a link to the [error catalog](https://stablevoy.com/docs/api/errors/); the ones you may want to handle on their own are `AuthenticationError`, `ValidationError` (with `issues`), `NotFoundError`, `RateLimitedError` and `MaintenanceError`. `TransportError` means no answer at all.

Reads, and creates that carry an idempotency key, are retried on rate limits, maintenance and failed connections, at most twice and only for waits of up to 10 seconds. Anything longer reaches you with `retry_after_seconds`, so a request never hangs. Every request times out after 30 seconds.

```python
from stablevoy import RetryPolicy, Stablevoy

stablevoy = Stablevoy.create(api_key, retries=RetryPolicy(max_retries=3, max_wait_seconds=30), timeout_seconds=10)
```

## Links

- [API reference](https://stablevoy.com/docs/api/)
- [Docs](https://stablevoy.com/docs/)
- [PHP SDK](https://github.com/stablevoy/stablevoy-php), [Node.js SDK](https://github.com/stablevoy/stablevoy-node)
- [WooCommerce plugin](https://wordpress.org/plugins/stablevoy-for-woocommerce/)

## License

MIT

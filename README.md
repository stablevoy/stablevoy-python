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

The buyer has the store's payment window to pay, or the platform default when the store sets none (`stablevoy.platform.limits()` gives it and the bounds). Pass `expires_in_minutes` (15 to 10080, that is 7 days) to set it for one invoice, for example a day or more for an invoice you send by email.

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

## Cancel an unpaid invoice

When the order is cancelled before the buyer pays, cancel its invoice. The payment page then tells the buyer not to pay, and the webhook `invoice.cancelled` is sent. Cancelling it again returns it unchanged.

```python
from stablevoy import ApiError

try:
    invoice = stablevoy.invoices.cancel(invoice_id)
except ApiError as error:
    if error.code != ApiError.INVOICE_NOT_CANCELLABLE:
        raise
    # A payment has already been seen on chain: fulfil or refund the order instead.
```

Money that still arrives after a cancel reaches your payout wallet as always and makes the invoice `paid_late`.

A store can have up to 1,000 invoices awaiting payment at once; over that `invoices.create()` fails with `ApiError.OPEN_INVOICE_LIMIT_REACHED`, so cancel the ones you no longer need. `stablevoy.platform.limits()` gives this and the other per-store limits.

## Totals for a period

Count the invoices of a period and add up what they brought, instead of walking the list. Pass a ready-made period or your own UTC days; one request covers at most 92 days, so ask for a year in four parts.

```python
from stablevoy import SummaryPeriod

week = stablevoy.invoices.summary(period=SummaryPeriod.LAST_7_DAYS)
print(week.invoice_count, week.invoices_by_status["paid"], week.invoiced_usd_cents, week.received_usd_micros)
for total in week.by_network:
    print(total.network, total.token, total.received_usd_micros)

october = stablevoy.invoices.summary(created_from="2026-10-01", created_to="2026-10-31")
```

`invoiced_usd_cents` leaves out cancelled and expired invoices. `received_usd_micros` (millionths of a dollar, as a string) counts the confirmed payments that passed sanctions screening.

## Unmatched transfers

On Tron the buyer pays your own wallet and the last digits of the amount pick the invoice. A transfer whose amount matched no invoice, usually from an exchange that took its fee out of it, is listed here. Attach it to an invoice in the Stablevoy dashboard; an API key can only read the list.

```python
for transfer in stablevoy.unmatched_transfers.list():
    print(transfer.amount_usd_micros, transfer.from_address, transfer.explorer_tx_url + transfer.tx_hash.removeprefix("0x"))
```

The payout wallet belongs to your account, not to one store, so each transfer has `shared_with_stores`: 1 means it is certainly this store's, more means it may belong to any of that many of your stores.

## Check the store before going live

Invoices need a payout wallet for at least one network the store accepts; without one every invoice is refused with `payout_address_not_set`. An EVM payout wallet that is a smart contract wallet or an EIP-7702 delegation must be confirmed in the dashboard, and confirmed again when it changes; until then new invoices leave out the EVM networks, and a store with nothing else is refused with `payout_address_unacknowledged`. Read the store of the key to find out in advance, and tell the merchant about networks buyers will not be offered:

```python
store = stablevoy.stores.current()
if not store.can_accept_payments():
    ...  # Hide the payment method: set the payout address in the Stablevoy dashboard first.
if store.networks_without_payout:
    ...  # These enabled networks have no payout wallet, so buyers do not see them.
if store.evm_payout_needs_review():
    ...  # The EVM payout wallet is not confirmed: store.evm_networks_blocked are not offered until the merchant reviews it in the dashboard.
```

## Connect a shop in one click

A shop integration can get its API key and webhook secret without the merchant copying them: it sends the merchant to the Stablevoy dashboard with a PKCE challenge, gets a code back on its callback URL and redeems it. This call needs no API key, since the shop has none yet. The code works once, so the call is never retried.

```python
from stablevoy import StablevoyConnect

connected = StablevoyConnect.create().exchange(code=code, code_verifier=code_verifier, site="https://shop.example.com")
# Store connected.api_key and connected.webhook_secret; connected.store_name is the store the merchant chose.
```

When the merchant disconnects the shop, give the key up so it stops working at once. A key that is already revoked raises `AuthenticationError`, which for a disconnect means the same:

```python
stablevoy.stores.revoke_current_key()
```

## Verify webhooks

Stablevoy posts an event to your webhook URL when an invoice is paid, overpaid, underpaid, expired, paid late or put on hold. One more, `invoice.payment_flagged`, comes when a later transfer to an invoice that is already paid is flagged by sanctions screening: the invoice keeps its paid status, so this event is not a new payment; the flagged transfer is in `event.data["payment"]`. Another, `store.payout_attention`, comes when the EVM payout wallet of the account becomes unconfirmed and again when it is fine: it carries no invoice, `event.data["payout"]` has the new `status`, the `blockedNetworks` and a `dashboardUrl`; read `stablevoy.stores.current()` again for the current state. Check the signature before you trust it, using the signing secret shown when you set the webhook in the dashboard. Pass the raw body, exactly as received.

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

## Check a pasted key

API keys are `svk_live_...` or `svk_test_...` and webhook signing secrets `svwhsec_...`; both end in a checksum. Keys made before this format (`sk_live_`, `sk_test_`, `whsec_`) keep working.

```python
from stablevoy import KeyCheck, check_api_key

if check_api_key(value) is KeyCheck.MISTYPED:
    print("A character is wrong or missing: copy the key again from the dashboard.")
```

`check_api_key` and `check_webhook_secret` answer `OK`, `MISTYPED` or `NOT_A_KEY`, without any request.

## Errors and retries

Every error extends `StablevoyError`. API errors are `ApiError` with the HTTP `status`, a stable `code`, a readable `detail` and a link to the [error catalog](https://stablevoy.com/docs/api/errors/); the ones you may want to handle on their own are `AuthenticationError`, `ValidationError` (with `issues`), `NotFoundError`, `RateLimitedError` and `MaintenanceError`. `TransportError` means no answer at all.

Reads, and creates that carry an idempotency key, are retried on rate limits, maintenance, gateway errors while the API restarts (502, 504, 520 to 524) and failed connections, at most twice and only for waits of up to 10 seconds. Anything longer reaches you with `retry_after_seconds`, so a request never hangs. Every request times out after 30 seconds.

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

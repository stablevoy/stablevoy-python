# Changelog

## Unreleased

- One-click connect: `StablevoyConnect.create().exchange(code=..., code_verifier=..., site=...)` redeems a connect code for the shop's API key and webhook secret (`ConnectedStore`). It needs no API key and is never retried, since the code works once.
- `stores.revoke_current_key()` revokes the key of the client, for a shop that disconnects. It is retried like a read.
- `Transport` has `delete()`. Your own implementation of `Transport` needs it too.
- Reads, and creates that carry an idempotency key, are also retried on the gateway errors 502, 504 and 520 to 524. nginx and Cloudflare answer with them for the few seconds the API restarts, so a call made then no longer fails at once. A 500 is still not retried.

## 1.2.0

- `Store` carries `networks_without_payout`: the enabled networks with no payout wallet for their family (EVM or Tron) on the account. Buyers are not offered them.
- `Store.can_accept_payments()` is false when no enabled network has a payout wallet, so every invoice would be refused. Check it before offering the payment method.
- `ApiError.PAYOUT_ADDRESS_NOT_SET` names the error code an invoice gets in that case.

## 1.1.0

- `invoices.list()` and `all()` take more filters: `source` (payment link, WooCommerce, Easy Digital Downloads, WHMCS, an API key made by hand, or not recorded; see `InvoiceSource`), `created_from` and `created_to` (UTC days as YYYY-MM-DD, both ends included) and `search` (an invoice id or the start of the external reference).
- Invoices carry `source` (`InvoiceSource`): how the invoice was made and, for a key, which one, on `list()`, `all()`, `get()` and `create()`.

## 1.0.1

- The timeout now bounds the whole request. Before, it only fired when the server went silent for that long, so a server sending its answer one byte at a time could keep a request open forever. A request out of time is cut off and retried where a repeat is safe, otherwise reported as a `TransportError`.
- An answer cut short or malformed at the HTTP level is a `TransportError` too; before, the standard library's `http.client` exception escaped as is.
- `timeout_seconds` must be more than 0 and at most 600; other values are refused with a `ConfigurationError` when the client is created.
- Security review of the change: certificate checks are unchanged (the default verified context), the watchdog timer is always cancelled, and no error message carries the key.

## 1.0.0

First release: invoices (create with an idempotency key, read, list and walk all pages), the store of the API key, limits, pricing and networks, typed errors with retries where a repeat is safe, and webhook signature verification. No dependencies, Python 3.11 or newer, fully typed.

Security: the base URL must be https (http only for localhost) and only a host, invoice ids must be UUIDs, redirects are never followed and every request has a timeout, so the API key cannot leak or reach another path.

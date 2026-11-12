# Changelog

## 1.8.0

- A store can pay out to its own address instead of the account one (set in the dashboard). `Store.payout_addresses` are now the addresses this store's new invoices use; `Store.payout_sources` (`PayoutSources`) says for each family whether it is the store's own (`PayoutSources.STORE`) or the account's (`PayoutSources.ACCOUNT`); `Store.account_payout_addresses` lists the account addresses. `evm_payout_status` and `evm_networks_blocked` follow the EVM address the store uses.
- `Store.archived_at`: when the store was archived, None while it is not.
- The webhook types `api_key.leaked` and `webhook_secret.leaked` are documented, and `store.payout_attention` carries `payout.source`.
- These need the API with store payout addresses (November 2026); an older answer without the new store fields is refused as an unexpected response.

## 1.7.0

- Stablevoy is moving to its own key formats: API keys `svk_live_...` / `svk_test_...` and webhook signing secrets `svwhsec_...`, each ending in a checksum. The SDK accepts them and the older `sk_live_` / `sk_test_` / `whsec_` in connect answers; older keys keep working.
- `check_api_key(value)` and `check_webhook_secret(value)` return a `KeyCheck`: `OK`, `MISTYPED` (a new-format key whose checksum does not match, so a character is wrong or missing) or `NOT_A_KEY`.

## 1.6.0

- `invoices.summary(period=...)` or `invoices.summary(created_from=..., created_to=...)`: totals of the invoices created in a range of UTC days (`InvoiceSummary`), with the count per status, the invoiced amount and the money received, also per network and token (`NetworkTotal`). Periods are in `SummaryPeriod`; one request covers at most 92 days, and a longer range is refused with `ApiError.INVALID_INVOICE_FILTER`.
- `unmatched_transfers.list()`: transfers to the payout wallet that matched no invoice, on the networks of the key's store (`UnmatchedTransfer`), each with `shared_with_stores`. Read only; they are attached to an invoice in the dashboard.
- `Limits` carries `api_keys_per_store` (`ApiKeysPerStore` with `plugin`, `mcp`, `api`), `open_invoices_per_store` and `invoices_per_minute_per_store`. New `ApiError.OPEN_INVOICE_LIMIT_REACHED`. These need the API of 7 November 2026; an older answer without them is refused as an unexpected response.
- `Stablevoy.__init__` takes `UnmatchedTransfers` as a fourth argument; `Stablevoy.create()` and `Stablevoy.from_transport()` are unchanged.

## 1.5.0

- `invoices.cancel(invoice_id)` cancels an invoice that is still waiting for its first payment: the payment page tells the buyer not to pay and the webhook `invoice.cancelled` is sent. Cancelling it again returns it unchanged. Once a payment has been seen the API refuses with `ApiError.INVOICE_NOT_CANCELLABLE`; money that still arrives after a cancel makes the invoice `paid_late`. New status `InvoiceStatus.CANCELLED` and webhook type `invoice.cancelled`.
- `invoices.create()` takes `expires_in_minutes`: how long the buyer has to pay this invoice, 15 to 10080 minutes (7 days). Outside the bounds the API answers `ApiError.INVALID_INVOICE_LIFETIME`.
- `Store.invoice_lifetime_minutes`: the store's payment window, None for the platform default. `Limits` carries `default_invoice_lifetime_minutes`, `min_invoice_lifetime_minutes` and `max_invoice_lifetime_minutes`.
- `Store.payout_addresses` (`PayoutAddresses` with `evm` and `tron`): the account's payout wallets per network family, None when not set. Read only; they are changed in the dashboard with a wallet signature.
- These fields need the API of 6 November 2026; an older answer without them is refused as an unexpected response.

## 1.4.0

- `Store` carries `evm_payout_status` (`plain`, `acknowledged`, `unacknowledged`, `unchecked`, or None without an EVM payout wallet, with `Store.EVM_PAYOUT_*` constants) and `evm_networks_blocked`: the enabled EVM networks new invoices leave out while the EVM payout wallet is not confirmed in the dashboard. `Store.evm_payout_needs_review()` tells it.
- `Store.can_accept_payments()` also counts the blocked EVM networks, so it is false for a store whose only networks are blocked.
- `ApiError.PAYOUT_ADDRESS_UNACKNOWLEDGED` names the error code an invoice gets when the EVM payout wallet is not confirmed and the store has no other network.
- New webhook type `store.payout_attention`: the EVM payout wallet of the account became unconfirmed, or is fine again. It carries no invoice; the data has `store` and `payout` (status, blocked networks, dashboard link).

## 1.3.0

- New webhook type `invoice.payment_flagged`: a payment of an invoice that is already paid, overpaid or paid late was flagged by sanctions screening. The invoice keeps its status; the flagged payment is in the event data under `payment`.
- `Store.connected_platform`: the plugin connected to the store in one click, or None. `Network` carries `forwarder_implementation`, `explorer_address_url` and `rpc_url`. `ApiError.limit_usd_cents` gives the limit an amount was refused for. All three were sent by the API and dropped.
- `invoices.list()` refuses a `limit` that is not a whole number (such as 5.5 or True) before sending, as Node does. Before, the API refused it.
- `invoices.create()` checks the idempotency key before sending: 1 to 255 printable ASCII characters without spaces, as the API requires. Before, a key with a line break or a non-ASCII letter failed inside http.client with an error outside `StablevoyError`.
- The search length is counted as the API counts it (UTF-16 units: an emoji is two), so a search the API would refuse is refused before it is sent.
- Webhook events now carry `source` on their invoice, as the API answers do. Events recorded before 3 November 2026 have none, and still verify.
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

# Changelog

## 1.0.1

- The timeout now bounds the whole request. Before, it only fired when the server went silent for that long, so a server sending its answer one byte at a time could keep a request open forever. A request out of time is cut off and retried where a repeat is safe, otherwise reported as a `TransportError`.
- An answer cut short or malformed at the HTTP level is a `TransportError` too; before, the standard library's `http.client` exception escaped as is.
- `timeout_seconds` must be more than 0 and at most 600; other values are refused with a `ConfigurationError` when the client is created.
- Security review of the change: certificate checks are unchanged (the default verified context), the watchdog timer is always cancelled, and no error message carries the key.

## 1.0.0

First release: invoices (create with an idempotency key, read, list and walk all pages), the store of the API key, limits, pricing and networks, typed errors with retries where a repeat is safe, and webhook signature verification. No dependencies, Python 3.11 or newer, fully typed.

Security: the base URL must be https (http only for localhost) and only a host, invoice ids must be UUIDs, redirects are never followed and every request has a timeout, so the API key cannot leak or reach another path.

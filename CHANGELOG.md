# Changelog

## 1.0.0

First release: invoices (create with an idempotency key, read, list and walk all pages), the store of the API key, limits, pricing and networks, typed errors with retries where a repeat is safe, and webhook signature verification. No dependencies, Python 3.11 or newer, fully typed.

Security: the base URL must be https (http only for localhost) and only a host, invoice ids must be UUIDs, redirects are never followed and every request has a timeout, so the API key cannot leak or reach another path.

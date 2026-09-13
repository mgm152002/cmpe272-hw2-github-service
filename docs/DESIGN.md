# Design Note

## Architecture

HTTP routes perform validation and delegate GitHub communication to `GitHubClient`. Webhook routes validate the signature against the untouched request bytes before parsing JSON. Accepted delivery summaries are stored in SQLite and exposed through `/events`.

The gateway is configured for one repository through environment variables. Request bodies reject undocumented fields, issue numbers and pagination values are range-checked, and all failures use the same `{error: {code, message, details}}` envelope.

## Errors and rate limits

Known GitHub 400/401/403/404/422 responses are translated into stable local errors. Primary, secondary, and explicit GitHub rate limits become 429 with `Retry-After`. Unexpected upstream failures, timeouts, and transport errors become 503. GET requests receive two short retries for transient failures; mutations are not retried because replay could duplicate side effects.

## Pagination

`page` and `per_page` are forwarded to GitHub. `per_page` is restricted to 100. GitHub's `Link` response header is forwarded unchanged so clients retain GitHub pagination semantics.

## Webhook idempotency and security

The receiver calculates HMAC SHA-256 over the raw body and uses constant-time comparison. SQLite uses `(delivery_id, action)` as a primary key, allowing GitHub retries to be acknowledged without duplicating stored events.

Only documented `issues`, `issue_comment`, and `ping` actions are accepted. Structured application logs include request and delivery identifiers plus safe event summaries; tokens, secrets, raw payloads, and signatures are excluded.

## Testing and packaging

Unit, contract, and mocked integration tests cover issue/comment workflows, webhook storage, error mapping, retries, pagination, logging, and the checked-in OpenAPI 3.1 contract. External calls are intercepted with `respx`, so CI requires no credentials. The Docker image runs as a non-root user and persists SQLite data through the Compose volume.

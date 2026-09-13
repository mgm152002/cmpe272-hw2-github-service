# CMPE 272 GitHub Issues Service

A production-grade, asynchronous FastAPI gateway for interacting with GitHub repository issues, comments, and signed webhooks. It abstracts GitHub API communication, exposes standard issue and comment operations, validates and stores signed GitHub webhooks with idempotency guarantees in SQLite, and provides structured observability.

## Team Members & Contributions

| Member | GitHub Username | Role / Contribution Area |
| --- | --- | --- |
| **Manoj Ganjigatte Manjunatha** | `@mgm152002` | Project scaffolding, core configuration, issue & comment workflows, CI/CD pipeline, and integration tests |
| **Vinayak Shivam Gupta** | `@vsh2504` | Webhook ingestion pipeline, HMAC SHA-256 signature verification, SQLite event persistence, structured JSON logging, and error handling |
| **Prajval Sudhir** | `@prajvalsudhir` | GitHub API client & resilience (retries, rate limiting), pagination utilities, OpenAPI 3.1 contract, reverse proxy setup, and documentation |

---

## 1. How to Run Locally

### Non-Docker Setup

#### Prerequisites
- Python 3.11+
- Virtual environment (`venv`)
- Target GitHub Personal Access Token (PAT)

#### Steps
1. Clone the repository and navigate to the root directory:
   ```bash
   cd cmpe272-hw2-github-service
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies in editable mode with development tools:
   ```bash
   python -m pip install -e ".[dev]"
   ```
4. Copy the environment configuration and fill in your values:
   ```bash
   cp .env.example .env
   ```
5. Start the development server with auto-reload:
   ```bash
   make run
   # or directly:
   uvicorn app.main:app --reload --port 8000
   ```
6. Access the interactive Swagger UI at `http://localhost:8000/docs` or OpenAPI spec at `http://localhost:8000/openapi.json`.

---

### Docker Setup

#### Run with Single Docker Image
1. Build the Docker container:
   ```bash
   make docker-build
   # or:
   docker build -t cmpe272-github-service .
   ```
2. Run the container with your `.env` file:
   ```bash
   docker run --rm --env-file .env -p 8000:8000 cmpe272-github-service
   ```

#### Run with Docker Compose
Docker Compose mounts a persistent volume for the SQLite event database and configures automatic container healthchecks:
```bash
docker compose up --build
```
To stop the services:
```bash
docker compose down
```

#### Run with Optional Local Reverse Proxy (Nginx)
The included `docker-compose.yaml` defines an optional Nginx reverse proxy configured in `nginx.conf` that listens on port `8080` and forwards requests to the FastAPI application:
```bash
docker compose --profile proxy up --build
```
Once running, you can access the service directly via the reverse proxy at `http://localhost:8080/healthz`.

---

## 2. Environment Variable Setup & Scopes Used

Copy the sample `.env.example` to create your local `.env`:
```bash
cp .env.example .env
```

### Configuration Parameters

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GITHUB_TOKEN` | **Yes** | `""` | GitHub Personal Access Token used for authenticated upstream API calls |
| `GITHUB_OWNER` | **Yes** | `""` | GitHub organization or account owner of the target repository |
| `GITHUB_REPO` | **Yes** | `""` | Target repository name |
| `WEBHOOK_SECRET` | **Yes** | `""` | Shared secret key configured in GitHub Webhooks for HMAC SHA-256 signature verification |
| `PORT` | No | `8000` | Port on which the FastAPI application listens |
| `DATABASE_PATH` | No | `data/events.db` | Filesystem path for SQLite event storage |

### GitHub Token Scopes Used

- **Fine-grained Personal Access Token (Recommended)**:
  - Repository Selection: **Only select repositories** (choose the configured target repository).
  - Repository Permissions:
    - **Issues**: `Read and write` (required to create, read, update, list issues and post comments).
    - **Metadata**: `Read-only` (mandatory default scope for repository access).
- **Classic Personal Access Token**:
  - For private repositories: select the **`repo`** scope.
  - For public repositories: select the **`public_repo`** scope.
- **Webhook Authentication**:
  - Webhooks sent by GitHub do **not** use the `GITHUB_TOKEN`.
  - GitHub computes an HMAC SHA-256 digest over the raw request payload using `WEBHOOK_SECRET`, transmitting it in the `X-Hub-Signature-256` header. The gateway independently validates this signature.

> **Security Note**: Never commit `.env` or personal access tokens to version control. The repository includes `.env` in `.gitignore`.

---

## 3. API Examples (curl & HTTPie)

Set your base URL variable:
```bash
export BASE_URL=http://localhost:8000
```

### Route Summary

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/healthz` | Health check endpoint |
| `POST` | `/issues` | Create a new repository issue |
| `GET` | `/issues` | List issues (with state, labels, and pagination) |
| `GET` | `/issues/{issue_number}` | Get a single issue by number |
| `PATCH` | `/issues/{issue_number}` | Update issue state, title, or body |
| `POST` | `/issues/{issue_number}/comments` | Create a comment on an issue |
| `GET` | `/issues/{issue_number}/comments` | List comments for an issue (with pagination) |
| `POST` | `/webhook` | Ingest signed GitHub webhook events |
| `GET` | `/events` | List stored webhook delivery summaries |

---

### 1. Health Check (`GET /healthz`)

**curl:**
```bash
curl --fail-with-body "$BASE_URL/healthz"
```

**HTTPie:**
```bash
http GET "$BASE_URL/healthz"
```

---

### 2. Create an Issue (`POST /issues`)

**curl:**
```bash
curl --fail-with-body -X POST "$BASE_URL/issues" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug: Connection timeout under high load",
    "body": "Observed intermittent socket timeouts during stress testing.",
    "labels": ["bug", "backend"]
  }'
```

**HTTPie:**
```bash
http POST "$BASE_URL/issues" \
  title="Bug: Connection timeout under high load" \
  body="Observed intermittent socket timeouts during stress testing." \
  labels:='["bug", "backend"]'
```

---

### 3. List Issues (`GET /issues`)

**curl:**
```bash
curl -i --fail-with-body "$BASE_URL/issues?state=open&page=1&per_page=30&labels=bug"
```

**HTTPie:**
```bash
http GET "$BASE_URL/issues" state==open page==1 per_page==30 labels==bug
```

*Note: GitHub RFC 5988 pagination URLs are preserved in the response `Link` header.*

---

### 4. Get Single Issue (`GET /issues/{issue_number}`)

**curl:**
```bash
curl --fail-with-body "$BASE_URL/issues/1"
```

**HTTPie:**
```bash
http GET "$BASE_URL/issues/1"
```

---

### 5. Update or Close an Issue (`PATCH /issues/{issue_number}`)

**curl:**
```bash
curl --fail-with-body -X PATCH "$BASE_URL/issues/1" \
  -H "Content-Type: application/json" \
  -d '{"state": "closed"}'
```

**HTTPie:**
```bash
http PATCH "$BASE_URL/issues/1" state=closed
```

---

### 6. Create an Issue Comment (`POST /issues/{issue_number}/comments`)

**curl:**
```bash
curl --fail-with-body -X POST "$BASE_URL/issues/1/comments" \
  -H "Content-Type: application/json" \
  -d '{"body": "Investigating this issue now. Fixed in upcoming release."}'
```

**HTTPie:**
```bash
http POST "$BASE_URL/issues/1/comments" body="Investigating this issue now. Fixed in upcoming release."
```

---

### 7. List Comments on an Issue (`GET /issues/{issue_number}/comments`)

**curl:**
```bash
curl -i --fail-with-body "$BASE_URL/issues/1/comments?page=1&per_page=30"
```

**HTTPie:**
```bash
http GET "$BASE_URL/issues/1/comments" page==1 per_page==30
```

---

### 8. Send Signed Webhook Delivery (`POST /webhook`)

Generate an HMAC SHA-256 signature using your secret and send the request:

**curl:**
```bash
set -a; . ./.env; set +a

payload='{"action":"opened","issue":{"number":1}}'
signature=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

curl --fail-with-body -X POST "$BASE_URL/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -H "X-GitHub-Delivery: manual-delivery-001" \
  -H "X-Hub-Signature-256: sha256=$signature" \
  -d "$payload"
```

**HTTPie:**
```bash
set -a; . ./.env; set +a

payload='{"action":"opened","issue":{"number":1}}'
signature=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

http POST "$BASE_URL/webhook" \
  X-GitHub-Event:issues \
  X-GitHub-Delivery:manual-delivery-001 \
  X-Hub-Signature-256:"sha256=$signature" \
  action=opened \
  issue:='{"number":1}'
```

*Response: `204 No Content` on successful ingestion.*

---

### 9. List Stored Webhook Events (`GET /events`)

**curl:**
```bash
curl --fail-with-body "$BASE_URL/events?limit=20"
```

**HTTPie:**
```bash
http GET "$BASE_URL/events" limit==20
```

---

## 4. Webhook Setup Steps & Redelivery Instructions

### GitHub Webhook Setup Guide

1. **Expose your local endpoint**:
   Use an HTTPS tunneling utility (e.g., `ngrok`, `cloudflared`, or `localtunnel`):
   ```bash
   ngrok http 8000
   ```
   Copy the public forwarding URL (e.g., `https://abcdef.ngrok-free.app`).
2. **Navigate to GitHub Settings**:
   Go to your target GitHub repository: **Settings** \u2192 **Webhooks** \u2192 click **Add webhook**.
3. **Configure Webhook Parameters**:
   - **Payload URL**: `https://<your-tunnel-host>/webhook`
   - **Content type**: `application/json` (do not use `application/x-www-form-urlencoded`).
   - **Secret**: Set to the identical value specified in your `WEBHOOK_SECRET` environment variable.
   - **SSL verification**: Enable SSL verification.
4. **Select Event Triggers**:
   Choose **Let me select individual events**:
   - Check **Issues**
   - Check **Issue comments**
   - Check the webhook **Active** checkbox.
5. **Save Webhook**:
   Click **Add webhook**. GitHub immediately sends a `ping` event. The gateway validates the signature, logs the request context, and returns HTTP `204 No Content`.

### Redelivery & Idempotency Instructions

1. In your repository on GitHub, go to **Settings \u2192 Webhooks**, and select your webhook.
2. Scroll to the **Recent Deliveries** section.
3. Click any delivery row to inspect request headers, payload, and the response received (`204`).
4. Click the **Redeliver** button to replay the event.
5. **Deduplication Behavior**:
   - GitHub sends the exact same delivery ID (`X-GitHub-Delivery`).
   - The gateway validates the HMAC signature.
   - The service queries SQLite using the primary key `(delivery_id, action)`.
   - Recognizing an existing record, the gateway safely acknowledges the delivery with `204 No Content` without writing duplicate rows to SQLite.

---

## 5. /tests with Unit + Integration Tests and Fixtures

### Test Organization

The `/tests` directory contains 72 tests providing 94% code coverage:

```
tests/
\u251c\u2500\u2500 conftest.py                   # Pytest fixtures, test database setup, and mock helpers
\u251c\u2500\u2500 fixtures/                      # Sample payloads and recorded GitHub upstream JSON
\u2502   \u251c\u2500\u2500 github_error.json          # GitHub error response schema fixture
\u2502   \u251c\u2500\u2500 issue_opened.json          # GitHub issues webhook payload fixture
\u2502   \u2514\u2500\u2500 issue_comment_created.json # GitHub issue_comment webhook payload fixture
\u251c\u2500\u2500 unit/                          # Isolated component unit tests
\u2502   \u251c\u2500\u2500 test_health.py             # Health check endpoint verification
\u2502   \u251c\u2500\u2500 test_issue_validation.py   # Request model field validation tests
\u2502   \u251c\u2500\u2500 test_error_handlers.py     # FastAPI exception handler validation
\u2502   \u251c\u2500\u2500 test_error_mapping.py      # Upstream GitHub error code translation tests
\u2502   \u251c\u2500\u2500 test_github_client.py      # Upstream HTTP client retry and header tests
\u2502   \u251c\u2500\u2500 test_pagination.py         # RFC 5988 Link header parser tests
\u2502   \u251c\u2500\u2500 test_signature_service.py  # Constant-time HMAC SHA-256 verification tests
\u2502   \u251c\u2500\u2500 test_request_context.py    # Request ID and delivery ID middleware tests
\u2502   \u251c\u2500\u2500 test_event_repository.py   # SQLite database deduplication tests
\u2502   \u2514\u2500\u2500 test_webhook_service.py    # Webhook filtering and payload parsing tests
\u251c\u2500\u2500 integration/                   # Full-flow API tests with mocked GitHub responses
\u2502   \u251c\u2500\u2500 test_issue_api.py          # Complete issues & comments API route tests
\u2502   \u2514\u2500\u2500 test_webhook_api.py        # Webhook delivery and verification API route tests
\u2514\u2500\u2500 contract/                      # Schema conformance test suite
    \u2514\u2500\u2500 test_openapi_contract.py   # Validates routes and models match openapi.yaml
```

### Running the Tests

Execute the full test suite with coverage report:
```bash
make test
# or directly with pytest:
PYTHONPATH=. pytest -v --cov=app --cov-report=term-missing
```

Run specific test suites:
```bash
# Unit tests only
PYTHONPATH=. pytest tests/unit -v

# Integration tests only
PYTHONPATH=. pytest tests/integration -v

# Contract validation tests only
PYTHONPATH=. pytest tests/contract -v
```

All external GitHub API interactions are simulated using `respx` mock dispatchers, allowing the test suite and CI pipeline to run deterministically without internet access or real GitHub credentials.

---

## 6. Postman / Bruno Collections & HTTPie Guide

### Postman Setup

A ready-to-import Postman collection and environment are provided in the `/postman` directory:
- [`postman/collection.json`](postman/collection.json): Preconfigured requests for all endpoints with sample bodies and assertions.
- [`postman/local_environment.json`](postman/local_environment.json): Environment variables containing `baseUrl`, `issueNumber`, `deliveryId`, and `webhookSignature`.

#### How to Use:
1. Open Postman and click **Import**.
2. Select both `postman/collection.json` and `postman/local_environment.json`.
3. Set the active environment to **Local**.
4. Run requests individually or execute the complete test run via Postman Collection Runner.

### Bruno Setup

To import into [Bruno](https://www.usebruno.com/):
1. In Bruno, click **Open Collection** or **Import**.
2. Select the `postman/collection.json` file.
3. Define the collection variable `baseUrl` set to `http://localhost:8000`.

---

## 7. Dockerfile & Optional Reverse Proxy Setup

### Container Architecture (`Dockerfile`)
- **Base Image**: `python:3.12-slim` for minimal vulnerability surface area and fast startup times.
- **Unprivileged User**: Runs as `appuser` (`UID 1000`) rather than `root` to enforce least-privilege security.
- **Optimized Caching**: Copies dependency declarations (`pyproject.toml`) before source code to leverage Docker layer caching during incremental builds.
- **Health Verification**: Exposes port `8000` and configures uvicorn process execution.

### Service Orchestration (`docker-compose.yaml`)
- Declares the `api` service with automated healthchecks (`/healthz`).
- Defines persistent volume `events-data` mounted at `/service/data` to preserve the SQLite database across container restarts.
- Defines an optional `proxy` service utilizing `nginx:alpine` and configured via `nginx.conf`:
  ```bash
  # Launch with reverse proxy enabled
  docker compose --profile proxy up --build
  ```

---

## 8. Design Note (≤ 2 Pages)

### 1. Architecture Overview
The gateway is structured into clear architectural tiers:
- **API Routers** (`app/api/`): HTTP routing, query parsing, request model validation, and response serialization.
- **Middleware & Observability** (`app/middleware/`, `app/logging_config.py`): Injects unique request IDs (`X-Request-ID`) or extracts GitHub delivery IDs, emitting structured JSON logs for auditability.
- **Core Services & Client** (`app/clients/`, `app/services/`): Handles upstream communication via `GitHubClient` using `httpx.AsyncClient` with connection pooling, and HMAC SHA-256 verification in `SignatureService`.
- **Persistence** (`app/repositories/`, `app/database.py`): Thread-safe SQLite storage for webhook delivery audit logs.

```
       [ Client / GitHub Webhook ]
                   \u2502
                   \u25bc
     +---------------------------+
     |   Nginx Reverse Proxy     |  (Optional :8080)
     +---------------------------+
                   \u2502
                   \u25bc
     +---------------------------+
     | Request Context / Logger  |  (Assigns X-Request-ID / X-GitHub-Delivery)
     +---------------------------+
                   \u2502
        +----------+----------+
        \u2502                     \u2502
        \u25bc                     \u25bc
 [ Issue Routes ]        [ Webhook Route ]
        \u2502                     \u2502
        \u25bc                     \u25bc
+----------------+      +--------------------+
| GitHubClient   |      |  SignatureService  | (HMAC SHA-256 Raw Bytes)
| (Retry / Map)  |      +--------------------+
+----------------+                 \u2502
        \u2502                          \u25bc
        \u25bc                 +--------------------+
 [ GitHub REST ]        |  EventRepository   | (SQLite Deduplication)
                        +--------------------+
```

---

### 2. Error Mapping Strategy
All API errors return a standard JSON error envelope:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested issue was not found.",
    "details": null
  }
}
```

- **Client Validation (400 Bad Request)**: FastAPI/Pydantic validation errors (e.g. empty issue title, invalid state transition) are trapped and mapped to local code `VALIDATION_ERROR` with specific field details.
- **Upstream Mapping**:
  - `401 Unauthorized` / `403 Forbidden` \u2192 mapped to `UPSTREAM_AUTH_ERROR` / `UPSTREAM_FORBIDDEN`.
  - `404 Not Found` \u2192 mapped to `RESOURCE_NOT_FOUND`.
  - `422 Unprocessable Entity` \u2192 mapped to `UNPROCESSABLE_ENTITY`.
  - `500` / `502` / `504` \u2192 mapped to `503 Service Unavailable` (`UPSTREAM_UNAVAILABLE`).
- **Rate Limit Handling (429 Too Many Requests)**: GitHub primary and secondary rate limits (indicated by `X-RateLimit-Remaining: 0` or HTTP 403/429 with rate limit messages) are translated to HTTP `429` with `RATE_LIMITED` error code, propagating upstream `Retry-After` headers to callers.
- **Retry Policy**:
  - `GET` requests (idempotent operations) receive up to 2 automatic retries for transient connection errors and HTTP 5xx responses using exponential backoff.
  - Mutating operations (`POST`, `PATCH`) are **never retried automatically** to prevent unintended duplicate side effects (e.g. creating duplicate comments or issues).

---

### 3. Pagination Strategy
- Gateway endpoints accept standard GitHub query parameters: `page` (positive integer) and `per_page` (clamped between `1` and `100`).
- Parameters are validated before reaching upstream.
- Upstream GitHub responses provide RFC 5988 `Link` headers containing relation URLs (`next`, `prev`, `first`, `last`). The gateway parses and preserves this `Link` header in its downstream response, enabling standard HTTP client pagination without loss of cursor context.

---

### 4. Webhook Ingestion & Deduplication Strategy
- **Raw Byte Verification**: GitHub signature verification must be executed against the untouched raw byte stream (`request.body()`). JSON re-serialization often reorders keys or modifies spacing, invalidating signatures. The gateway reads the raw stream before body parsing.
- **Timing Attack Defense**: Verification uses `hmac.compare_digest` for constant-time comparison, eliminating side-channel timing vulnerabilities.
- **Event Filtering**: Only documented repository events (`ping`, `issues`, `issue_comment`) and actions (`opened`, `edited`, `closed`, `reopened`, `created`, `deleted`) are accepted. Unsupported events return `400 Bad Request`.
- **Database Deduplication**:
  - Webhook delivery summaries are stored with a composite primary key: `(delivery_id, action)`.
  - When GitHub redelivers an event, SQLite detects the duplicate primary key.
  - The service returns `204 No Content`, safely acknowledging GitHub's retry without duplicating stored records.

---

### 5. Security Trade-offs & Production Hardening
- **Strict Payload Schemas**: Pydantic models configure `extra = "forbid"` on mutating requests, preventing parameter injection and mass-assignment vulnerabilities.
- **Data Minimization in Persistence**: The service persists only operational metadata (`delivery_id`, `event`, `action`, `issue_number`, `timestamp`). Raw payloads, user tokens, webhook secrets, and signatures are **never** stored in SQLite.
- **Redacted Structured Logging**: Application logs use JSON format and include `request_id` and `delivery_id` for tracing. Authorization tokens and webhook secrets are explicitly scrubbed and excluded from logs.
- **Container Isolation**: Docker execution runs under a non-root user (`appuser`). In Docker Compose, the SQLite database directory is isolated inside an internal named volume.

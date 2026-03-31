---
name: api-integration
description: "Use this skill whenever the user wants to design, build, consume, test, or debug APIs and integrations between services. Triggers include: any mention of 'API', 'REST', 'RESTful', 'GraphQL', 'gRPC', 'WebSocket', 'webhook', 'endpoint', 'HTTP method', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'status code', 'request', 'response', 'JSON', 'XML', 'SOAP', 'API key', 'OAuth', 'OAuth2', 'JWT', 'Bearer token', 'API gateway', 'rate limiting', 'throttling', 'pagination', 'cursor', 'API versioning', 'OpenAPI', 'Swagger', 'Postman', 'curl', 'httpx', 'axios', 'fetch', 'API client', 'SDK generation', 'API documentation', 'retry logic', 'circuit breaker', 'idempotency', 'API testing', 'mock API', 'API wrapper', or any request to connect to an external service, consume a third-party API, design an API for a project, or troubleshoot API errors. Also use when the user shows HTTP status codes, API error messages, authentication failures, or asks 'how do I call this API?' or 'why is the API returning 403?'. If someone needs to connect two systems via HTTP, use this skill."
---

# API Integration Guide

Use this skill to design clean APIs, consume third-party services reliably, handle authentication securely, and build resilient integrations across REST, GraphQL, WebSockets, and webhooks.

## API Design Principles

### REST Fundamentals
Build RESTful APIs by treating resources as nouns, not verbs:
- Use `/users`, `/orders` — not `/getUsers`, `/createOrder`
- Map HTTP methods to CRUD: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)
- Nest resources for relationships: `GET /users/123/orders` (orders for user 123)
- Always use plural names: `/users/123`, not `/user/123`

**Why:** Consistency makes APIs intuitive and predictable for consumers.

### HTTP Status Codes
Use status codes correctly to signal intent:

**Success (2xx):**
- `200 OK` — Request succeeded, response body included
- `201 Created` — Resource created (include Location header with new resource URL)
- `204 No Content` — Success but no body (typical for DELETE)

**Client Error (4xx):**
- `400 Bad Request` — Malformed request or invalid input
- `401 Unauthorized` — Missing or invalid authentication
- `403 Forbidden` — Valid auth but insufficient permissions
- `404 Not Found` — Resource doesn't exist
- `409 Conflict` — Request conflicts with current state (e.g., duplicate key)
- `422 Unprocessable Entity` — Validation failed (include field-level errors)
- `429 Too Many Requests` — Rate limited (include Retry-After header)

**Server Error (5xx):**
- `500 Internal Server Error` — Unexpected error, safe to retry with backoff
- `502 Bad Gateway`, `503 Unavailable` — Dependency down, safe to retry
- `504 Gateway Timeout` — Request took too long, safe to retry

### Consistent Error Responses
Structure errors to help consumers debug:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": [
      {"field": "email", "message": "Must be a valid email address"},
      {"field": "age", "message": "Must be 18 or older"}
    ]
  }
}
```

**Why:** Structured errors let clients handle different failure types programmatically.

### API Versioning
Choose an explicit versioning strategy:
- **URL path (recommended):** `/api/v1/users` — visible, cacheable, obvious which version you're using
- **Header:** `Accept: application/vnd.custom+json; version=2` — clean URLs but harder to test/debug
- **Query param:** `/api/users?version=1` — easy but easy to forget

**Why:** URL versioning prevents surprises when the API evolves.

### Pagination
Choose pagination strategy based on scale:

**Offset-based** (`?page=3&per_page=25`):
- Simple to implement and test
- Problem: OFFSET becomes slow on large datasets (database must skip N rows)
- Use for: small datasets, admin panels

**Cursor-based** (`?cursor=<encoded>&limit=25`):
- Fast on large datasets (database jumps directly to cursor position)
- Stable when data is added/removed (offsets shift, cursors don't)
- Use for: real-time feeds, large result sets

**Keyset** (`?after_id=123&limit=25`):
- Cursor without encoding; works when IDs are sequential
- Fast and simple

Always include metadata:
```json
{
  "data": [...],
  "meta": {
    "total": 500,
    "page": 3,
    "per_page": 25,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTUwfQ=="
  }
}
```

**Why:** Pagination lets clients handle large datasets efficiently without memory blowup.

## Authentication & Authorization

### API Keys
Simplest auth for service-to-service communication:

```bash
# Correct: Bearer scheme in header (standard, logged safely)
curl -H "Authorization: Bearer abc123xyz" https://api.example.com/v1/users

# WRONG: Key in query param (logged in access logs, browser history)
curl https://api.example.com/v1/users?api_key=abc123xyz
```

**Implementation tips:**
- Rotate keys regularly (monthly or on leak)
- Scope keys to minimum permissions (read-only for public data)
- Use separate keys for dev/staging/production
- Revoke immediately if compromised

**Why:** API keys are simple but sacrifice security for convenience. Only use for internal services or public APIs with rate limiting.

### OAuth 2.0
Use when users grant third-party apps access to their data:

**Authorization Code Flow** (for web/mobile apps):
1. User redirected to auth provider's login
2. User grants permission
3. Auth provider redirects back with authorization code
4. App exchanges code for access token (server-to-server, secret never exposed to browser)
5. App uses token to call resource API

**Client Credentials Flow** (service-to-service, no user involved):
```python
import httpx

client = httpx.Client()
# Exchange client_id and client_secret for token
response = client.post(
    "https://auth.example.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": "my_app_id",
        "client_secret": "my_app_secret",
        "scope": "api:read"
    }
)
token = response.json()["access_token"]

# Use token for API calls
api_response = client.get(
    "https://api.example.com/v1/resources",
    headers={"Authorization": f"Bearer {token}"}
)
```

**PKCE** (required for SPAs and mobile apps):
- Prevents authorization code interception attacks
- Client generates random code_verifier, sends SHA256 hash (code_challenge)
- When exchanging code for token, sends original code_verifier
- Server verifies code_verifier matches code_challenge

**Token lifecycle:**
- Access token: short-lived (15–60 min), included in Authorization header
- Refresh token: long-lived (days/weeks), used to get new access tokens when expired
- Store access token in memory, refresh token in secure httpOnly cookie (web) or keychain (mobile)

**Why:** OAuth separates authentication (user login) from authorization (app permissions), letting users control what data apps access.

### JWT (JSON Web Tokens)
Stateless authentication—token payload includes user info:

```python
import jwt
import datetime

# Create token (server)
payload = {
    "sub": "user_123",  # Subject (user ID)
    "email": "user@example.com",
    "roles": ["admin"],
    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
    "iat": datetime.datetime.utcnow()
}
token = jwt.encode(payload, "secret_key", algorithm="HS256")

# Verify token (server, no DB lookup needed)
decoded = jwt.decode(token, "secret_key", algorithms=["HS256"])
print(decoded["sub"])  # user_123
```

**Best practices:**
- Set short expiry (15 min) to limit damage if token is stolen
- Use refresh tokens for longer sessions
- Never include sensitive data (password, SSN)—JWT is encoded, not encrypted
- Always validate: signature, expiry, issuer, audience

**Why:** JWTs eliminate database lookups for every request, but rely on asymmetric cryptography (private key to sign, public key to verify).

## Consuming APIs (HTTP Clients)

### Python (httpx)
```python
import httpx

# Synchronous client with retries
client = httpx.Client(
    base_url="https://api.example.com/v1",
    headers={"Authorization": f"Bearer {API_KEY}"},
    timeout=30.0,
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
)

try:
    response = client.get("/users", params={"page": 1})
    response.raise_for_status()  # Raise on 4xx/5xx
    users = response.json()
except httpx.HTTPStatusError as e:
    print(f"API error: {e.response.status_code}")
except httpx.TimeoutException:
    print("Request timed out")
finally:
    client.close()

# Async client for concurrent requests
async with httpx.AsyncClient(base_url="https://api.example.com/v1") as client:
    responses = await asyncio.gather(
        client.get("/users/1"),
        client.get("/users/2"),
        client.get("/users/3")
    )
```

### JavaScript/TypeScript (fetch / axios)
```javascript
// Fetch API (built-in, no dependencies)
const response = await fetch("https://api.example.com/v1/users", {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  signal: AbortSignal.timeout(30000)  // 30s timeout
});

if (!response.ok) {
  throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}
const data = await response.json();

// Axios with interceptors for auth refresh
const api = axios.create({
  baseURL: "https://api.example.com/v1",
  timeout: 30000,
  headers: { "Authorization": `Bearer ${ACCESS_TOKEN}` }
});

api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Token expired, refresh it
      const newToken = await refreshToken();
      api.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
      return api.request(error.config);  // Retry original request
    }
    return Promise.reject(error);
  }
);
```

### curl (Testing/Debugging)
```bash
# Simple GET
curl https://api.example.com/v1/users

# With authentication
curl -H "Authorization: Bearer <TOKEN>" https://api.example.com/v1/users

# POST with JSON body
curl -X POST https://api.example.com/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Debug: show response headers, HTTP status, timing
curl -w "\nStatus: %{http_code} | Time: %{time_total}s\n" \
  -sS -D - https://api.example.com/v1/health

# Trace request/response including headers
curl -v https://api.example.com/v1/users

# With custom header and follow redirects
curl -L -H "X-API-Key: secret" https://api.example.com/v1/users
```

## Resilience Patterns

### Retry with Exponential Backoff
Retry transient failures (5xx, timeouts) but not client errors (4xx):

```python
import time, random
import httpx

def retry_api_call(func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            # Don't retry 4xx (client's fault, will fail again)
            if hasattr(e, 'response') and 400 <= e.response.status_code < 500:
                raise

            if attempt == max_retries - 1:
                raise

            # Exponential backoff + jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s...")
            time.sleep(delay)

# Use it
def fetch_users():
    response = httpx.get("https://api.example.com/v1/users")
    response.raise_for_status()
    return response.json()

users = retry_api_call(fetch_users)
```

**Why:** Exponential backoff prevents overwhelming a recovering service. Jitter prevents thundering herd (all clients retrying simultaneously).

### Timeouts
Always set timeouts—never wait forever:

```python
# Python httpx
client = httpx.Client(timeout=30.0)  # 30s total timeout

# Or specify connect/read separately
client = httpx.Client(timeout=httpx.Timeout(
    connect=5.0,   # How long to establish connection
    read=30.0,     # How long to wait for response
    write=5.0,
    pool=5.0
))

# JavaScript fetch
signal = AbortSignal.timeout(10000)  // 10s
const response = await fetch(url, { signal });
```

**Why:** Hanging requests leak resources. Timeouts prevent cascading failures.

### Idempotency
Make requests safe to retry—same request twice = same result:

```python
import uuid

# Client sends unique request ID
idempotency_key = str(uuid.uuid4())
response = httpx.post(
    "https://api.example.com/v1/payments",
    json={"amount": 100, "currency": "USD"},
    headers={"Idempotency-Key": idempotency_key}
)

# Server deduplicates: if same Idempotency-Key comes again, return cached response
# Without this, network retry could charge customer twice
```

**Why:** Network errors force retries. Idempotency keys prevent duplicate operations (payment charged twice, order created twice).

### Circuit Breaker
Stop calling a failing service to prevent cascading failures:

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,           # Open after 5 failures
    reset_timeout=60,     # Try again after 60s (half-open state)
    listeners=[...]       # Log state changes
)

@breaker
def call_external_api():
    return httpx.get("https://slow-service.example.com/api")

try:
    result = call_external_api()
except CircuitBreaker.CircuitBreakerError:
    # Service is down, use fallback
    return cached_data or error_response()
```

**Why:** Circuit breaker prevents hammering a dead service and lets it recover.

## WebSockets

Use for real-time data (chat, live notifications, streaming):

```javascript
const ws = new WebSocket("wss://api.example.com/stream");

ws.addEventListener("open", () => {
  // Authenticate after connection
  ws.send(JSON.stringify({ type: "auth", token: AUTH_TOKEN }));
  // Subscribe to events
  ws.send(JSON.stringify({ type: "subscribe", channel: "orders" }));
});

ws.addEventListener("message", (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "order_update") {
    console.log("Order:", msg.data);
  }
});

ws.addEventListener("close", () => {
  // Reconnect with backoff
  setTimeout(() => location.reload(), 5000);
});

ws.addEventListener("error", (error) => {
  console.error("WebSocket error:", error);
});
```

**Patterns:**
- Message framing: send JSON with `type` field for routing
- Heartbeat: send ping/pong every 30s to detect dead connections
- Reconnection: auto-reconnect with exponential backoff

## Webhooks

Webhooks = server pushes data to you (reverse API):

```python
# Receiving webhooks (Flask example)
from flask import request
import hmac, hashlib

@app.post("/webhooks/stripe")
def handle_stripe_webhook():
    # Verify signature (HMAC-SHA256 of body with secret)
    signature = request.headers.get("Stripe-Signature")
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return {"error": "Invalid signature"}, 401

    # Track webhook ID to prevent duplicate processing
    event_id = request.json["id"]
    if WebhookLog.find(event_id):
        return {"status": "ok"}, 200  # Already processed

    # Process async, return 200 immediately
    queue.enqueue(process_webhook_event, request.json)
    WebhookLog.create(event_id)

    return {"status": "received"}, 200
```

**Patterns:**
- Return 200 immediately, process async (webhooks time out after 5-30s)
- Verify signatures with HMAC-SHA256 (don't trust source IP alone)
- Track event IDs to handle retries idempotently
- Respect retries: sender retries on non-2xx responses, so handlers must be idempotent

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| **401 Unauthorized** | Expired token, wrong auth header, missing Bearer | Check token expiry, refresh if needed, verify header format |
| **403 Forbidden** | Valid auth but insufficient permissions | Check API key/token scope, verify you have required role |
| **404 Not Found** | Wrong URL, resource deleted, case-sensitive path | Check endpoint URL, verify trailing slashes, test with curl |
| **429 Too Many Requests** | Rate limited | Implement backoff, check Retry-After header, reduce request rate |
| **500 Internal Server Error** | Server bug | Retry with backoff, check API status page, contact support |
| **Timeout** | Request took too long | Increase timeout, check server health, verify network path |
| **CORS error** (browser only) | Missing access-control headers | Server must send Access-Control-Allow-Origin, check browser console |
| **SSL/TLS error** | Certificate issue | Check cert expiry with `openssl s_client -connect api.example.com:443` |

## Testing APIs

- **Manual:** Use curl, Postman, or Insomnia to test endpoints
- **Unit tests:** Mock external API with fixtures, test error handling
- **Integration tests:** Test against staging API or containerized mock server
- **Contract tests:** Verify API response matches OpenAPI spec
- **Load testing:** Use k6 or JMeter to find breaking points

## API Documentation

Publish interactive docs to help consumers:
- **OpenAPI/Swagger:** Standard specification, auto-generated from code (FastAPI does this) or hand-written
- **Redoc, Swagger UI, Scalar:** Interactive documentation with try-it-out
- **Include:** authentication examples, error responses, rate limits, pagination examples

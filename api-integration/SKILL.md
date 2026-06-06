---
name: api-integration
description: "Use this when: my API keeps returning 401 or 403, getting 429 rate limit errors, integrate a third-party API, my requests keep timing out, add retry logic with backoff, design a REST API, handle OAuth2 authentication, paginate API responses, CORS errors blocking my requests, secure API keys properly, build consistent error responses, my webhook isn't receiving events, OpenAPI, JWT, circuit breaker, idempotency key, API versioning, rate limiting, token refresh"
---

# API Integration

## Identity
You are an API integration engineer. Design for resilience and consistency — the contract between services is sacred. Never expose credentials in query params, URLs, or logs.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| HTTP client (Python) | httpx | Async-native, timeout config, `raise_for_status` |
| HTTP client (JS) | axios | Interceptors for auth refresh, consistent error model |
| Auth standard | OAuth2 + JWT | Stateless, scoped, short-lived tokens |
| Versioning | URL path `/api/v1/` | Visible, cacheable, trivially testable with curl |
| Pagination (small) | offset + limit | Simple; acceptable under 10k rows |
| Pagination (large) | cursor-based | Fast at scale; stable when data is inserted/deleted |
| Error format | `{"error":{"code":"...","message":"...","details":[]}}` | Programmatically handleable |
| Spec | OpenAPI / Swagger | Auto-generate clients, docs, contract tests |
| Retry library | tenacity (Python) | Declarative retry + backoff policy |
| Resilience | pybreaker / circuitbreaker | Prevent cascading failures |

## Decision Framework

### Auth Method
- If user grants 3rd-party access → OAuth2 Authorization Code + PKCE
- If service-to-service, no user → OAuth2 Client Credentials
- If simple internal service → API key in `Authorization: Bearer` header
- Never → API key in query string (written to every access log)

### Status Codes
- Create succeeds → `201 Created` + `Location` header pointing to new resource
- Delete succeeds → `204 No Content` (no body)
- Validation fails → `422 Unprocessable Entity` with per-field `details`
- Rate limited → `429 Too Many Requests` + `Retry-After` header
- Default → `400` (client fault) or `500` (server fault)

### Retry Logic
- If `5xx` or network timeout → retry with exponential backoff + jitter
- If `4xx` → never retry (client error; will fail identically again)
- If `429` → pause for `Retry-After` value, then retry
- Default → 3 retries, base 1s delay, cap at 30s

### Pagination Strategy
- If dataset < 10k rows → offset (`?page=N&per_page=25`)
- If real-time feed or large dataset → cursor (`?cursor=<token>&limit=25`)
- Always include `has_more` and `next_cursor` in the response envelope

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| `?api_key=secret` in URL | Written to access logs and browser history | `Authorization: Bearer <key>` header |
| Retry all error types | 4xx retries waste quota and mask bugs | Retry only `5xx` and timeouts |
| `time.sleep(2)` in retry loops | Fixed delay causes thundering herd on recovery | Exponential backoff + random jitter |
| Return `200 OK` for errors | Client error detection fails silently | Correct `4xx`/`5xx` codes always |
| JWT without `exp` claim | Stolen token is valid forever | 15-min expiry + refresh token rotation |
| Offset pagination on large tables | `OFFSET 100000` is a full sequential scan | Cursor or keyset pagination |
| No timeout on external calls | Hanging requests cascade failures | Set connect (5s) + read (30s) timeouts separately |

## Quality Gates
- [ ] Status codes match semantics (201 for create, 204 for delete, 422 for validation)
- [ ] Credentials only in `Authorization` header — never in URLs or logs
- [ ] Retry logic skips all `4xx`; retries `5xx` and timeouts only
- [ ] Idempotency key sent on all mutable requests that may be retried
- [ ] Error responses include machine-readable `code` field alongside `message`
- [ ] HTTP client has explicit connect + read timeouts on every instance

## Reference
```
GET    /api/v1/users         → 200 + list body
POST   /api/v1/users         → 201 + Location header
GET    /api/v1/users/{id}    → 200 or 404
PUT    /api/v1/users/{id}    → 200 full replace
PATCH  /api/v1/users/{id}    → 200 partial update
DELETE /api/v1/users/{id}    → 204 No Content
```

---

## Resilient API Call Pattern (Python/httpx + tenacity)

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

def is_transient(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(is_transient),
    reraise=True,
)
def call_api(token: str, resource_id: str) -> dict:
    with httpx.Client(
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0)
    ) as client:
        response = client.get(
            f"https://api.example.com/v1/resources/{resource_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()

try:
    data = call_api(token=get_token(), resource_id="abc123")
except httpx.HTTPStatusError as e:
    logger.error("client_error", status=e.response.status_code)
except httpx.HTTPError as e:
    logger.error("api_unavailable", error=str(e))
```

## Webhook Pattern

```python
import hmac, hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("X-Webhook-Signature", "")
    if not verify_webhook(payload, sig, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    event = json.loads(payload)
    event_id = event["id"]
    
    # Idempotency: skip already-processed events
    if await redis.exists(f"webhook:{event_id}"):
        return {"status": "duplicate"}
    
    # Return 200 immediately; process async
    background_tasks.add_task(process_event, event)
    await redis.setex(f"webhook:{event_id}", 86400, "1")
    return {"status": "accepted"}
```

## OAuth2 Token Lifecycle

```
Access token: 15–60 min expiry; keep in memory (not localStorage)
Refresh token: longer-lived; rotate on use; revoke old token immediately

Flow:
  1. Request access + refresh tokens (code grant + PKCE or client credentials)
  2. Store access token in memory, refresh token in httpOnly cookie
  3. On 401: use refresh token to get new access token
  4. On refresh token expiry: redirect to login
```

## Pagination Patterns

```python
# Cursor-based (large datasets)
def get_all_records(base_url: str, token: str) -> list:
    results, cursor = [], None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(base_url, params=params,
                            headers={"Authorization": f"Bearer {token}"}).json()
        results.extend(resp["items"])
        if not resp.get("has_more"):
            break
        cursor = resp["next_cursor"]
    return results
```

## Circuit Breaker

```python
from pybreaker import CircuitBreaker

# Open after 5 consecutive failures; wait 60s before half-open probe
breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
def call_payment_service(payload):
    return requests.post(PAYMENT_URL, json=payload, timeout=10)
```

When open: return cached/degraded response; log + alert. Don't let one slow service starve others.

## Monitoring Health Endpoints

```
GET /health    → 200 if alive, 503 if degraded
GET /ready     → 200 when ready to serve traffic (post-startup checks)

Response: {"status": "healthy", "checks": {"db": "ok", "cache": "ok"}}
```

Use Uptime Kuma, Healthchecks.io, or a simple cron calling `/health` for alerting.

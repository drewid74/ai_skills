---
trigger: "I need to design, build, test, monitor, or debug API integrations, webhooks, service orchestration, browser automation, OAuth flows, or integration health dashboards"
name: "API Integration Engineer"
domain: "Integration Architecture & Reliability"
description: "Universal specialist consolidating REST/GraphQL/WebSocket API design, OAuth2/JWT auth, resilience patterns, service orchestration, webhook management, browser automation, and integration monitoring. Explains WHY behind every pattern with code examples."
confidence: "high"
complexity: "expert"
---

# API Integration Engineer

This is a domain-owning specialist that consolidates three expertise areas: API integration fundamentals, service orchestration & messaging, and browser automation into one unified integrations architect. The skill provides patterns, architecture guidance, tooling expertise, and explains the WHY behind each decision.

## Core Principles

### WHY REST/GraphQL/WebSocket Matter

**REST** provides stateless, cacheable, scalable integration. Each endpoint maps to a resource with standard HTTP verbs. WHY: Simplicity, maturity, broad tooling support, easy to reason about.

**GraphQL** solves REST's over-fetching/under-fetching by letting clients specify exact fields. WHY: Network efficiency, single query reduces round-trips, strong typing prevents bugs.

**WebSocket** enables real-time bidirectional communication without polling. WHY: Latency-critical apps (chat, monitoring dashboards, live data feeds), eliminates wasteful HTTP overhead.

---

## I. API Design & Architecture

### 1. REST API Maturity Model (Richardson Maturity)

**Level 0: RPC** — Everything POST to `/api/action`. Violates REST principles.
```python
# Don't do this
POST /api/action?action=getUser&id=123
```

**Level 1: Resources** — Use URL paths for resources, not actions.
```python
# Better
GET /api/users/123
```

**Level 2: HTTP Methods** — Use GET/POST/PUT/DELETE semantically.
```python
# Best practice
GET    /api/users       # List
POST   /api/users       # Create
GET    /api/users/123   # Retrieve
PUT    /api/users/123   # Replace
PATCH  /api/users/123   # Partial update
DELETE /api/users/123   # Delete
```

WHY: Semantic clarity allows caching proxies, CDNs, and clients to understand operations. GET requests are idempotent and cacheable; DELETE is repeatable safely. Standard verbs reduce cognitive load.

### 2. API Versioning Strategy

**URL Path** — `/v1/users`, `/v2/users`. Simple, explicit, allows parallel versions.
```python
# Clear version in URL
GET /v2/users/123
GET /v1/users/123  # Deprecated endpoint still works
```

**Header-Based** — `Accept: application/vnd.myapi.v2+json`. Cleaner URLs, harder to route.

**Query Parameter** — `/users?apiVersion=2`. Conflicts with semantic query params.

WHY: Path-based versioning is most operationally clear. It allows different infrastructure per version, explicit deprecation timelines, and prevents accidents with stale clients.

Breaking changes (renamed fields, removed endpoints, changed response structure) require new versions. Non-breaking additions (new fields with defaults) don't.

### 3. API Design Quality Scoring

Evaluate APIs against OpenAPI 3.1 spec with these dimensions:

**Authentication** (20pts)
- Clear auth method documented (+5)
- Scopes defined for OAuth (+5)
- Token refresh flow documented (+5)
- Examples with credentials in docs (+5)

**Error Handling** (20pts)
- Consistent HTTP status codes (+5)
- Error response has `code`, `message`, `details` (+5)
- Includes `x-request-id` for tracing (+5)
- Deprecation warnings in headers (+5)

**Resilience** (20pts)
- Rate limit headers (`X-RateLimit-*`) (+5)
- Retry-After for 429/503 (+5)
- Timeout guidance in docs (+5)
- Idempotency key support (+5)

**Operability** (20pts)
- Comprehensive OpenAPI spec (+5)
- Example requests/responses for each endpoint (+5)
- Webhook signature validation documented (+5)
- Health check endpoint documented (+5)

**Design** (20pts)
- Consistent field naming (snake_case/camelCase) (+5)
- Pagination strategy documented (+5)
- Filtering/sorting documented (+5)
- No leaky abstractions (db column names exposed) (+5)

```yaml
# API Quality Audit Result
audit:
  authentication: 18/20  # Missing explicit token refresh examples
  error_handling: 15/20  # Missing request IDs
  resilience: 12/20      # No retry guidance
  operability: 16/20     # Incomplete OpenAPI
  design: 19/20
  overall_score: 80/100
  
breaking_changes_detected:
  - field_rename: { old: "user_id", new: "userId" }
  - endpoint_removed: "/v1/legacy/accounts"
  - response_structure_change: { path: "/users/{id}", details: "birthDate field now object not string" }
```

### 4. HTTP Client Libraries

Different languages and async requirements demand different HTTP clients:

**Python**: `httpx` is the modern async choice. `requests` for sync. WHY: httpx supports async/await, connection pooling, automatic decompression.

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/data")
```

**JavaScript**: `axios` with interceptors for error handling, `fetch` API with AbortController for cancellation. WHY: axios has built-in request/response interceptors, simplifies error standardization. Fetch with AbortController cancels hanging requests.

```javascript
const controller = new AbortController();
fetch(url, { signal: controller.signal });
controller.abort(); // Cancel request
```

**Debugging**: curl flags `-w` (timing), `-D` (response headers to file), `-v` (verbose trace), `-i` (include headers). WHY: These reveal network timing, redirects, actual headers sent—critical for API debugging.

```bash
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/endpoint
# -w shows time_connect, time_total, http_code
curl -D headers.txt https://api.example.com/endpoint
curl -v https://api.example.com/endpoint  # Full request/response trace
```

---

## II. Authentication & Authorization

### 1. OAuth2 Flow Generator

OAuth2 solves the problem: "How do I authorize third-party apps without sharing passwords?" WHY: Users keep passwords private, apps get scoped access, easy token revocation.

**Authorization Code Flow** (Standard for web apps)
```python
# Step 1: Client redirects user to authorization server
auth_url = f"https://auth.provider.com/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=read:users&state={random_state}"

# Step 2: User approves, browser redirects to callback with code
# GET https://myapp.com/callback?code=auth_code&state=...

# Step 3: Backend exchanges code for token (with client_secret, never in browser)
import requests
token_response = requests.post(
    "https://auth.provider.com/token",
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,  # Backend only
        "redirect_uri": REDIRECT_URI
    }
)
access_token = token_response.json()["access_token"]
```

WHY: Authorization code flow never exposes tokens to browser. Client secret stays backend-only. User controls what scopes the app receives.

**Client Credentials Flow** (Service-to-service)
```python
# No user involved, app authenticates directly
token_response = requests.post(
    "https://auth.provider.com/token",
    data={
        "grant_type": "client_credentials",
        "client_id": SERVICE_ID,
        "client_secret": SERVICE_SECRET,
        "scope": "write:logs read:config"
    }
)
```

WHY: Used when no user interaction needed (background jobs, service-to-service APIs).

**Refresh Token Rotation** (Security best practice)
```python
# Access tokens are short-lived (1h)
# Refresh tokens are long-lived (30d) but rotated
if token_expired():
    response = requests.post(
        "https://auth.provider.com/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": old_refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    new_access_token = response.json()["access_token"]
    new_refresh_token = response.json()["refresh_token"]  # Rotated
    store_securely(new_refresh_token)
```

WHY: If access token is stolen, compromise is limited (1h window). Rotating refresh tokens prevents indefinite abuse if refresh token leaks.

### 1.5. PKCE (Proof Key for Code Exchange)

PKCE protects single-page applications (SPAs) and mobile apps from authorization code interception attacks. WHY: SPAs can't securely store client secrets (they run in browser), so PKCE uses a code verifier/challenge exchange instead.

```python
# SPA flow with PKCE
import secrets
import hashlib
import base64

code_verifier = secrets.token_urlsafe(32)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip("=")

# Step 1: Redirect with challenge
auth_url = f"https://auth.provider.com/authorize?client_id={CLIENT_ID}&code_challenge={code_challenge}&code_challenge_method=S256&redirect_uri={REDIRECT_URI}&state={random_state}"

# Step 2: Exchange code with verifier (no client secret needed)
token_response = requests.post(
    "https://auth.provider.com/token",
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "code_verifier": code_verifier,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI
    }
)
```

WHY: Even if attacker intercepts auth code, they can't use it without the original code_verifier. Essential for public clients (mobile, SPAs).

### 2. JWT Claims & Scopes

JWT (JSON Web Token) encodes claims (user ID, scopes, expiration) in a signed token. WHY: Stateless authentication, no database lookups per request, easy to distribute across microservices.

```python
# JWT Structure: header.payload.signature
# Payload example:
import jwt
payload = {
    "sub": "user_123",           # Subject (who)
    "email": "alice@example.com",
    "scopes": ["read:files", "write:files"],
    "aud": "api.myapp.com",      # Audience (who can use this)
    "iat": 1704067200,           # Issued at
    "exp": 1704070800            # Expires (1 hour)
}
token = jwt.encode(payload, SECRET, algorithm="HS256")

# On API request
@app.post("/files")
def create_file(request):
    token = request.headers["Authorization"].split(" ")[1]
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    
    if "write:files" not in claims["scopes"]:
        raise PermissionDenied()
    # Create file...
```

WHY: JWT is compact, doesn't require session storage, scales horizontally (any server can verify).

### 3. gRPC & SOAP (Protocol Alternatives)

**gRPC**: High-performance RPC using Protocol Buffers and HTTP/2. Ideal for microservice-to-microservice communication. WHY: Binary encoding is 3-10x faster than JSON, HTTP/2 multiplexing reduces connection overhead, strong typing prevents bugs.

```protobuf
service UserService {
  rpc GetUser (UserId) returns (User) {}
  rpc ListUsers (Empty) returns (stream User) {}
}
```

**SOAP**: Legacy enterprise integration with XML over HTTP. Still used in banking, healthcare. WHY: Enterprise standardization, strict contracts, guaranteed message delivery patterns.

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <GetUser><userId>123</userId></GetUser>
  </soapenv:Body>
</soapenv:Envelope>
```

WHY gRPC over SOAP: gRPC is 2-5x faster, easier to maintain. SOAP for legacy enterprise systems with strict WS-* security requirements.

---

## III. Resilience Patterns

### 1. Retry with Exponential Backoff

Transient failures (network blips, 503 Service Unavailable) should retry. Permanent failures (401 Unauthorized, 404 Not Found) should not.

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """WHY: Exponential backoff prevents thundering herd when service recovers"""
    for attempt in range(max_retries):
        try:
            return func()
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential: 1s, 2s, 4s, 8s...
            delay = base_delay * (2 ** attempt)
            # Jitter: add randomness to prevent synchronized retries
            delay += random.uniform(0, delay * 0.1)
            print(f"Retry {attempt + 1} after {delay:.1f}s")
            time.sleep(delay)

# Usage
def fetch_data():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

data = retry_with_backoff(fetch_data)
```

WHY: Immediate retries hammer a struggling service. Exponential backoff gives it recovery time. Jitter prevents multiple clients from retrying in lockstep (thundering herd).

### 2. Circuit Breaker Pattern

Once a service fails consistently, stop hammering it. Open the circuit, fail fast, then try again periodically.

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal, requests pass through
    OPEN = "open"          # Failing, requests fail immediately
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            # Success: reset
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def fetch_upstream():
    response = requests.get("https://upstream.api.com/data")
    response.raise_for_status()
    return response.json()

try:
    data = breaker.call(fetch_upstream)
except Exception as e:
    print(f"Failed: {e}")
```

WHY: Without circuit breaker, timeouts cascade. Service A hammers struggling Service B, exhausts resources. Circuit breaker fails fast (immediately), lets B recover, then retries in HALF_OPEN state.

### 3. Bulkhead Pattern (Isolation)

Partition resources so one failing endpoint doesn't exhaust the whole pool.

```python
from concurrent.futures import ThreadPoolExecutor

class Bulkhead:
    """WHY: Isolate thread pools so slow endpoints don't starve fast ones"""
    def __init__(self, name, max_threads):
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self.name = name
    
    def call(self, func, *args, **kwargs):
        future = self.executor.submit(func, *args, **kwargs)
        return future.result()

# Separate bulkheads for different services
auth_bulkhead = Bulkhead("auth", max_threads=10)
analytics_bulkhead = Bulkhead("analytics", max_threads=3)

# If analytics is slow, auth still has 10 threads available
def call_auth():
    return auth_bulkhead.call(requests.get, "https://auth.service/verify")

def call_analytics():
    return analytics_bulkhead.call(requests.post, "https://analytics/event")
```

WHY: Thread pool exhaustion cascades. One slow endpoint (slow database query) hangs all other requests. Separate pools per dependency isolate the blast radius.

### 4. Rate Limiting (Server & Client)

**Server-side:** Protect API from abuse.
```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # client_id -> list of timestamps
    
    def is_allowed(self, client_id):
        now = datetime.now()
        # Purge old requests outside window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]
        
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        return False

limiter = RateLimiter(max_requests=100, window_seconds=60)

@app.post("/api/data")
def create_data(request):
    if not limiter.is_allowed(request.client_id):
        return JSONResponse(
            {"error": "Rate limit exceeded"},
            status_code=429,
            headers={
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "Retry-After": "30"
            }
        )
```

**Client-side:** Respect upstream limits.
```python
import time

def call_with_rate_limit(url, requests_per_second=10):
    """WHY: Client-side limiting prevents hitting rate limits, improves reliability"""
    delay = 1.0 / requests_per_second
    time.sleep(delay)
    return requests.get(url)
```

WHY: Server rate limit protects against overload. Client-side limit respects the upstream's constraints gracefully.

---

## IV. Service Orchestration & Messaging

### 1. Event-Driven Architecture

Instead of synchronous request chains, services emit events that others consume asynchronously.

**Kafka/RabbitMQ Pattern:**
```python
# Publisher
import json
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

def user_signed_up(user_id, email):
    event = {
        "event_type": "user.signup",
        "user_id": user_id,
        "email": email,
        "timestamp": "2025-01-15T10:30:00Z"
    }
    producer.send("user-events", json.dumps(event).encode())

# Consumer
from kafka import KafkaConsumer

consumer = KafkaConsumer('user-events', group_id='email-service')

for message in consumer:
    event = json.loads(message.value)
    if event["event_type"] == "user.signup":
        send_welcome_email(event["email"])
```

WHY: Decouples email service from user service. User signup completes immediately; email sends async. If email service is down, events queue in RabbitMQ, process when it recovers.

**Redis Streams** (simpler alternative):
```python
import redis

r = redis.Redis()

def emit_event(stream, event_data):
    r.xadd(stream, event_data)

def consume_events(stream, consumer_group):
    r.xgroup_create(stream, consumer_group, id='0', mkstream=True)
    while True:
        messages = r.xreadgroup(
            {stream: '>'},
            consumer_group,
            count=1,
            block=0
        )
        # Process messages...
```

### 2. Webhook Pattern & Debugger

Webhooks let external services push data to you instead of polling.

**Signature Verification** (Security):
```python
import hmac
import hashlib

WEBHOOK_SECRET = "your-secret"

def verify_webhook(payload, signature):
    """WHY: Signature proves the webhook came from trusted source"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.post("/webhook/github")
def github_webhook(request):
    signature = request.headers.get("X-Hub-Signature-256", "").split("=")[1]
    payload = request.body
    
    if not verify_webhook(payload, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)
    
    event = json.loads(payload)
    if event["action"] == "opened":
        process_pr_opened(event)
```

**Webhook Debugger Dashboard:**
```yaml
# Track webhook delivery
webhooks:
  github_pr_events:
    url: "https://myapp.com/webhook/github"
    last_delivery: "2025-01-15T14:32:10Z"
    status: "success"
    response_time: "245ms"
    retry_count: 0
    
  stripe_payments:
    url: "https://myapp.com/webhook/stripe"
    last_delivery: "2025-01-15T14:31:45Z"
    status: "failure"
    response_time: "timeout"
    retry_count: 3
    next_retry: "2025-01-15T14:35:45Z"
    
  slack_notifications:
    url: "https://myapp.com/webhook/slack"
    last_delivery: "2025-01-15T13:15:22Z"
    status: "success"
    response_time: "312ms"
    retry_count: 1
```

WHY: Webhook debugger shows delivery status, allows retry simulation, prevents lost notifications.

### 3. Workflow Orchestration (Low-Code Platforms)

**n8n**: Self-hosted, Docker-native workflow builder. WHY: Full control over data, privacy-friendly, extends with custom functions, ideal for on-premise requirements.

**Node-RED**: IoT/MQTT-focused flow-based development. WHY: Native MQTT nodes, perfect for IoT pipelines, lightweight, runs on Raspberry Pi.

**Make/Zapier**: Cloud-based automation. WHY: No infrastructure management, 1000+ pre-built connectors, easiest onboarding for non-technical teams.

Example workflow: Listen to GitHub webhook → Extract PR metadata → Post to Slack → Log to analytics event stream. Low-code platforms eliminate custom glue code.

### 4. Notification Services

**Ntfy**: Simple HTTP pub/sub with browser notifications. WHY: No auth, dead simple REST API, self-hosted option.

**Gotify**: Self-hosted push notification server. WHY: Similar to Ntfy but more feature-rich (user management, priorities), Docker deployable.

**Apprise**: Unified 80+ notification providers (Slack, Discord, Telegram, SMS, PagerDuty). WHY: Single API for all notification channels, prevents vendor lock-in.

**Healthchecks.io**: Cron job monitoring with webhooks. WHY: Detects hung jobs, missed schedules, notifies on failure.

Example: Failed API integration triggers Apprise → sends to Slack AND PagerDuty AND SMS. Single code path, multiple channels.

---

## V. Browser Automation & Scraping

### 1. Playwright Patterns

**Anti-bot Evasion:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        args=[
            "--disable-blink-features=AutomationControlled",
        ]
    )
    context = browser.new_context(
        # Mimic real browser
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        viewport={"width": 1280, "height": 720},
        timezone_id="America/New_York",
        locale="en-US",
    )
    
    # Mask Playwright detection
    page = context.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    """)
    
    page.goto("https://example.com")
```

WHY: Sites detect Playwright/Selenium via `navigator.webdriver`. Hiding it mimics real user, bypasses anti-bot checks.

**Content Extraction:**
```python
# Extract data with CSS selectors
products = page.query_selector_all("div.product-card")
for product in products:
    name = product.query_selector(".product-name").text_content()
    price = product.query_selector(".price").text_content()
    print(f"{name}: {price}")

# XPath for complex queries
reviews = page.query_selector_all("//div[@class='review' and @data-rating>4]")
```

WHY: CSS selectors are fast; XPath is more powerful for conditional queries.

**Page Monitoring (Detect Changes):**
```python
def monitor_page(url, check_interval=300):
    """WHY: Poll for changes instead of manual checks"""
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        
        while True:
            page.goto(url)
            content = page.content()
            
            # Hash content to detect changes
            current_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if current_hash != last_hash:
                alert_user(f"Page changed: {url}")
                last_hash = current_hash
            
            time.sleep(check_interval)
```

### 2. Content Extraction Patterns

**Structured Table Extraction**: Parse HTML tables into CSV/JSON.
```python
tables = page.query_selector_all("table")
for row in page.query_selector_all("tr"):
    cells = row.query_selector_all("td")
    print([cell.text_content() for cell in cells])
```

**Pagination Handling**: Follow next-page links until exhausted. WHY: Prevents incomplete data collection on multi-page sites.

**Infinite Scroll Detection**: Use `page.evaluate()` to detect scroll height changes, load more content dynamically. WHY: JS-heavy sites load content on scroll; static parsing misses data.

### 3. Anti-Bot Defense Specifics

Major providers: **Cloudflare** (WAF rules), **Akamai** (bot detection), **PerimeterX** (behavioral analysis), **DataDome** (machine learning). WHY: These services track browser fingerprints, request patterns, TLS signatures.

**FlareSolverr**: Headless browser proxy that bypasses Cloudflare challenges. WHY: Routes requests through real Chrome, solves CAPTCHA challenges automatically. Self-hosted alternative to commercial unblocking services.

Example: Cloudflare detected your IP → FlareSolverr solves challenge → returns cookies → subsequent requests succeed.

### 4. Ethical Scraping Checklist

- **robots.txt**: Respect disallowed paths; check User-Agent rules.
- **Rate Limiting**: 1-2 second delays between requests; use Retry-After headers.
- **User-Agent**: Set meaningful identifier (company name, email) so site admins can contact you.
- **ToS Compliance**: Check terms of service; automated scraping may be forbidden.
- **Personal Data**: Never scrape PII without consent; comply with GDPR/CCPA.
- **API Preference**: Always use official APIs first. Scraping is last resort.

WHY: Ethical scraping maintains site viability, prevents IP bans, reduces legal risk, respects creator intent.

---

## VI. New Capabilities: API Health & Testing

### 1. Reverse Proxy & Service Discovery

**Traefik**: Auto-discovers Docker container labels, routes traffic by hostname/path. WHY: Eliminates manual config, self-healing, integrates with Let's Encrypt.

**Nginx Proxy Manager**: Web UI for managing reverse proxies, SSL certificates. WHY: Easier than raw Nginx, no need to edit config files directly.

**Cloudflare Tunnels**: Zero-trust tunneling from private network to Cloudflare edge. WHY: No public IP needed, DDoS protection, WAF built-in, works behind NAT/firewall.

Example: Private API on office network → Cloudflare Tunnel → accessible globally over HTTPS with no port forwarding.

### 2. Health Monitoring

**Uptime Kuma**: Self-hosted status monitoring, ping checks, webhook alerts. WHY: Open-source, beautiful dashboards, cheaper than Pingdom/Statuspage.

**Health Check Endpoints**: Expose `/health` (basic liveness), `/ready` (readiness to serve), `/live` (Kubernetes liveness). WHY: Orchestrators use these to detect hung services and auto-restart.

```python
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
def readiness_check():
    # Check database, cache, external APIs
    if not check_database():
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
```

---

## VII. New Capabilities: API Health & Testing

### 1. API Test Suite Generator

Scan OpenAPI spec, auto-generate comprehensive test suites:

```python
# From OpenAPI spec, generate tests
def generate_tests_from_openapi(spec_path):
    """
    WHY: Automation reduces manual test writing, ensures coverage
    Generates:
    - Happy path (valid inputs)
    - Edge cases (null, empty, max values)
    - Auth flows (valid token, expired, invalid)
    - Error cases (4xx, 5xx)
    """
    spec = load_openapi(spec_path)
    
    tests = []
    for path, operations in spec["paths"].items():
        for method, details in operations.items():
            # Happy path
            tests.append({
                "name": f"{method.upper()} {path} - success",
                "method": method,
                "path": path,
                "auth": "valid_token",
                "body": generate_valid_payload(details)
            })
            
            # Missing required field
            tests.append({
                "name": f"{method.upper()} {path} - missing_field",
                "method": method,
                "path": path,
                "auth": "valid_token",
                "body": remove_required_field(details),
                "expect_status": 400
            })
            
            # Unauthorized
            tests.append({
                "name": f"{method.upper()} {path} - unauthorized",
                "method": method,
                "path": path,
                "auth": None,
                "expect_status": 401
            })
    
    return tests
```

### 2. Integration Health Dashboard

Monitor in real-time:
```yaml
integration_health:
  api_response_times:
    stripe_api:
      p50: 145ms
      p95: 450ms
      p99: 890ms
      trend: "stable"
    
    mailgun_api:
      p50: 200ms
      p95: 600ms
      p99: "timeout"
      trend: "degrading"
  
  webhook_delivery_rates:
    github_pushes:
      delivered: 1247
      failed: 3
      success_rate: "99.76%"
      avg_latency: "234ms"
    
    stripe_charges:
      delivered: 5621
      failed: 14
      success_rate: "99.75%"
      avg_latency: "156ms"
  
  queue_depths:
    email_notifications: 234
    sms_notifications: 12
    analytics_events: 4567
  
  error_budget:
    monthly_allowed_errors: 43200  # 99.9% uptime
    used_this_month: 8910
    remaining: 34290
    burn_rate: "high"  # Using budget 2x faster than expected
```

---

## Summary: WHY This Matters

APIs are how systems communicate. Good API design prevents bugs, scaling nightmares, and security breaches. Resilience patterns (retry, circuit breaker, bulkhead) prevent cascading failures. Event-driven architecture scales better than synchronous chains. Webhook debuggers and health dashboards prevent silent data loss. OAuth2 flows protect user privacy.

This skill consolidates patterns from REST API maturity, OAuth2 security, messaging systems (Kafka, RabbitMQ), browser automation, and operational excellence into one integrations architect domain.
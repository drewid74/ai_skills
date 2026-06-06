---
name: service-integration
description: >-
  Connect and orchestrate services using n8n, Redis Streams, MQTT, webhooks,
  and REST. Build automation workflows, event-driven pipelines, service health
  monitoring with Uptime Kuma, and Traefik reverse proxy routing.
triggers:
  - "automate workflow between services"
  - "set up n8n"
  - "connect services with webhooks"
  - "MQTT broker integration"
  - "Redis Streams event pipeline"
  - "Traefik routing and labels"
  - "Uptime Kuma health monitoring"
  - "build service mesh"
tags: [n8n, redis-streams, mqtt, traefik, webhook, uptime-kuma, automation]
author: merged
---

# Service Integration

## Identity

Wire services together reliably. Default to event-driven over polling. Every integration needs a retry strategy and a dead-letter path. Use n8n for no-code automation; Redis Streams for high-throughput pipelines; MQTT for IoT/sensor data.

## Stack Defaults

| Component | Default | Notes |
|-----------|---------|-------|
| Workflow automation | n8n | Self-hosted, visual, 400+ integrations |
| Message streaming | Redis Streams | XADD/XREADGROUP for ordered delivery |
| IoT messaging | Mosquitto (MQTT) | eclipse-mosquitto:latest |
| Reverse proxy | Traefik v3 | Label-based routing, auto TLS |
| Service monitoring | Uptime Kuma | HTTP/TCP/ping checks, Slack alerts |
| Webhook security | HMAC-SHA256 | X-Hub-Signature-256 header |
| HTTP client | httpx + tenacity | Async, retry with backoff |

## Decision Framework

```
IF integrating two services:
  → Prefer event-driven (webhook/stream) over polling
  → Define payload schema before connecting
  → Add HMAC verification on inbound webhooks

IF choosing message transport:
  → n8n: user-facing automations, low-throughput workflows
  → Redis Streams: high-throughput, ordered, consumer groups
  → MQTT: IoT/sensors, publish-subscribe with retained topics
  → HTTP webhook: external services (GitHub, Stripe, Slack)

IF service goes down:
  → Redis Streams: consumer group holds pending entries, retry on recovery
  → n8n: workflow executions have retry on fail + error workflow
  → MQTT QoS 1: broker stores undelivered messages for reconnect

IF adding to Traefik:
  → Add labels to docker-compose service
  → Use certresolver for automatic TLS
  → Define middleware for auth/rate-limit

IF monitoring is needed:
  → Uptime Kuma HTTP check every 60s
  → Alert on: 2 consecutive failures
  → Notify: Slack + email
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Polling external APIs every second | Webhooks + Redis Streams |
| No retry on external HTTP calls | tenacity with exponential backoff |
| Secrets in compose env plaintext | `.env` file + docker secrets |
| Webhook without signature verification | HMAC-SHA256 on every inbound webhook |
| Single consumer reading all streams | Consumer groups for parallel processing |
| Traefik without TLS | `tls.certresolver: letsencrypt` always |

## Quality Gates

- [ ] All webhooks verify HMAC signature before processing
- [ ] Redis Streams consumers use consumer groups (not raw XREAD)
- [ ] n8n error workflow configured for each production flow
- [ ] Traefik dashboard not exposed on public port
- [ ] Uptime Kuma alert fires within 3 min of outage
- [ ] Integration tests simulate webhook delivery with real signatures

→ See `docker-selfhost` for base compose network setup  
→ See `api-integration` for HTTP resilience patterns (circuit breaker, retry)  
→ See `sigint-osint-feeds` for high-volume Redis Streams worker patterns

---

## n8n Docker Compose

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      N8N_HOST: n8n.yourdomain.com
      N8N_PORT: 5678
      N8N_PROTOCOL: https
      WEBHOOK_URL: https://n8n.yourdomain.com/
      GENERIC_TIMEZONE: America/Chicago
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: ${DB_USER}
      DB_POSTGRESDB_PASSWORD: ${DB_PASS}
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - internal
      - web
    labels:
      traefik.enable: "true"
      traefik.http.routers.n8n.rule: "Host(`n8n.yourdomain.com`)"
      traefik.http.routers.n8n.tls.certresolver: "letsencrypt"
      traefik.http.services.n8n.loadbalancer.server.port: "5678"
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - n8n_postgres:/var/lib/postgresql/data
    networks:
      - internal

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - internal

volumes:
  n8n_data:
  n8n_postgres:
  redis_data:

networks:
  internal:
    driver: bridge
  web:
    external: true
```

## Traefik Reverse Proxy

```yaml
# traefik/docker-compose.yml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--certificatesresolvers.letsencrypt.acme.email=you@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_acme:/acme
    networks:
      - web
    labels:
      traefik.enable: "true"
      traefik.http.routers.traefik.rule: "Host(`traefik.yourdomain.com`)"
      traefik.http.routers.traefik.tls.certresolver: "letsencrypt"
      traefik.http.routers.traefik.service: "api@internal"
      traefik.http.routers.traefik.middlewares: "auth"
      traefik.http.middlewares.auth.basicauth.users: "${TRAEFIK_USERS}"

volumes:
  traefik_acme:

networks:
  web:
    external: true
```

### Add service to Traefik (labels pattern)

```yaml
# In any service's docker-compose.yml:
labels:
  traefik.enable: "true"
  traefik.http.routers.myapp.rule: "Host(`myapp.yourdomain.com`)"
  traefik.http.routers.myapp.tls.certresolver: "letsencrypt"
  traefik.http.services.myapp.loadbalancer.server.port: "8080"
  # Optional: IP whitelist middleware
  traefik.http.routers.myapp.middlewares: "ipwhitelist"
  traefik.http.middlewares.ipwhitelist.ipwhitelist.sourcerange: "192.168.0.0/16,10.0.0.0/8"
networks:
  - web
```

## Redis Streams Event Pipeline

```python
import redis
import json
from typing import Any

r = redis.Redis(host="redis", port=6379, decode_responses=True)

# Producer: push event to stream
def publish_event(stream: str, event_type: str, payload: dict[str, Any]):
    r.xadd(
        stream,
        {"type": event_type, "data": json.dumps(payload)},
        maxlen=10_000,       # Trim stream to last 10K events
        approximate=True     # MAXLEN ~ (allows Radix tree optimization)
    )

# Consumer: reliable processing with consumer groups
def create_consumer_group(stream: str, group: str):
    try:
        r.xgroup_create(stream, group, id="$", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

def consume_events(stream: str, group: str, consumer: str, handler):
    while True:
        messages = r.xreadgroup(
            group, consumer, {stream: ">"},
            count=50, block=2000   # Block 2s if empty
        )
        for _, entries in (messages or []):
            for msg_id, data in entries:
                try:
                    handler(json.loads(data["data"]))
                    r.xack(stream, group, msg_id)
                except Exception as e:
                    print(f"Failed {msg_id}: {e}")
                    # Message stays in pending; retry after timeout
```

## MQTT with Mosquitto

```yaml
# mosquitto/docker-compose.yml
services:
  mosquitto:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"      # WebSocket
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log

volumes:
  mosquitto_data:
  mosquitto_log:
```

```
# mosquitto.conf
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwords

listener 9001
protocol websockets

persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

### Python MQTT client

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe("sensors/#", qos=1)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"Topic: {msg.topic}, Data: {payload}")

client = mqtt.Client()
client.username_pw_set("user", "password")
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, keepalive=60)
client.loop_forever()
```

## Webhook HMAC Verification

```python
import hmac
import hashlib
from fastapi import Request, HTTPException

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

async def verify_webhook(request: Request) -> bytes:
    """Verify GitHub-style HMAC-SHA256 webhook signature."""
    body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        raise HTTPException(403, "Missing signature")

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(403, "Invalid signature")

    return body
```

## Uptime Kuma

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - uptime_data:/app/data
    networks:
      - web
    labels:
      traefik.enable: "true"
      traefik.http.routers.uptime.rule: "Host(`status.yourdomain.com`)"
      traefik.http.routers.uptime.tls.certresolver: "letsencrypt"
      traefik.http.services.uptime.loadbalancer.server.port: "3001"

volumes:
  uptime_data:
```

Configure checks in UI: New Monitor → HTTP/HTTPS → URL + interval (60s) + notification (Slack/email) → "Heartbeat/Down after 2 retries"

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| n8n webhook not receiving | Traefik WEBHOOK_URL mismatch | Set `WEBHOOK_URL=https://n8n.domain.com/` (trailing slash) |
| Redis Stream consumer stuck | Pending entries not ACK'd | `XPENDING stream group` then `XCLAIM` stale entries |
| MQTT client disconnects | Keepalive timeout | Increase `keepalive=120`; add reconnect loop |
| Traefik 404 on service | Service not on `web` network | Add `networks: [web]` to service in compose |
| Webhook 403 Invalid signature | Signature computed on wrong body | Compute HMAC on raw bytes BEFORE parsing |
| n8n workflow silently fails | No error workflow | Add "On Error" trigger workflow with notification node |

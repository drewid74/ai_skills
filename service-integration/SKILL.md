---
name: service-integration
description: "Use this skill whenever the user wants to connect, orchestrate, or automate workflows across multiple services, platforms, or tools. Triggers include: any mention of 'integration', 'workflow automation', 'n8n', 'Node-RED', 'Zapier', 'Make', 'IFTTT', 'webhook', 'event-driven', 'message queue', 'RabbitMQ', 'Redis Streams', 'NATS', 'Kafka', 'MQTT', 'pub/sub', 'event bus', 'notification', 'Discord bot', 'Slack bot', 'Telegram bot', 'Ntfy', 'Gotify', 'Apprise', 'Pushover', 'email notification', 'SMTP', 'cron job', 'scheduled task', 'data pipeline', 'ETL', 'sync', 'bridge', 'connector', 'middleware', 'service mesh', 'Traefik', 'reverse proxy', 'service discovery', 'health check', 'uptime monitoring', 'Uptime Kuma', 'Healthchecks.io', or requests to make services talk to each other, trigger actions on events, build notification pipelines, or orchestrate multi-step workflows across platforms. Also use when the user asks 'how do I get X to notify Y?', 'connect my NAS to my dashboard', 'automate this workflow', or wants to build any kind of cross-service automation. If someone describes a manual multi-step process that could be automated, use this skill."
---

## Overview

Patterns for connecting services into automated, event-driven workflows. Covers workflow orchestration platforms, message queues, notification pipelines, reverse proxies, health monitoring, and common integration patterns for self-hosted infrastructure.

## Workflow Orchestration Platforms

### n8n (Self-Hosted, Recommended)

Deploy n8n as your primary workflow orchestration engine. It provides visual workflow builder with 400+ integrations, supports JavaScript/Python code nodes, and handles branching, error handling, and data transformation.

**Docker Compose deployment:**
```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.example.com
      - N8N_PROTOCOL=https
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
    networks:
      - services

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - services

volumes:
  n8n_data:
  postgres_data:

networks:
  services:
```

**Common workflow triggers:** webhook (REST API), cron (scheduled), app event (database change), manual (UI button).

**Why n8n:** Complex multi-step workflows with branching, data transformation, and reusable subworkflows. Code nodes let you write custom JavaScript/Python when UI blocks aren't enough. Built-in error handling retries and conditional paths.

### Node-RED

Use Node-RED for IoT-heavy automation and MQTT event processing. Visual flow editor similar to n8n but optimized for sensor data and home automation.

```bash
docker run -d \
  --name nodered \
  -p 1880:1880 \
  -v nodered_data:/data \
  nodered/node-red:latest
```

**Best for:** IoT/home automation, MQTT event processing, simple linear data flows. Extensible palette via community npm nodes.

### Zapier / Make (Cloud-Based)

Use cloud platforms when integrating SaaS services with no API access or when non-technical team members need to build automations. Trade-off: data leaves your infrastructure and monthly cost scales with usage.

### Custom Scripts (Bash/Python)

Deploy simple, predictable automations as cron jobs or systemd timers. Best for linear workflows without branching.

```bash
#!/bin/bash
# Backup and notify
backup_db() && curl -d "Backup complete" ntfy.example.com/backups || \
  curl -d "Backup failed" ntfy.example.com/backups
```

## Message Queue & Event Bus Patterns

### When You Need a Queue

- **Decouple producers and consumers:** sender doesn't wait for receiver to process
- **Handle traffic spikes:** queue absorbs burst; consumers process at their pace
- **Guarantee delivery:** messages persist even if consumer is down
- **Fan-out:** one event triggers multiple consumers

### Redis Streams

Lightweight queue built into Redis. Use for homelab scale workflows.

```python
# Producer: add event to stream
redis_client.xadd('workflow:events', {'event': 'file_uploaded', 'file_id': '123'})

# Consumer: read with consumer group (ensures each message processed once)
messages = redis_client.xreadgroup('workflow:group', 'consumer1', {'workflow:events': '>'})
for message in messages:
    process(message)
    redis_client.xack('workflow:events', 'workflow:group', message[0])
```

### MQTT (Publish/Subscribe)

Designed for IoT, lightweight, hierarchical topics. Deploy Mosquitto broker:

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_config:/mosquitto/config
```

**Topic hierarchy:** `home/sensor/temperature`, `home/sensor/humidity`, `home/appliance/washer/status`.

**QoS levels:** 0 (fire-and-forget), 1 (at least once), 2 (exactly once).

### NATS

Cloud-native messaging, extremely fast. Modes: pub/sub, request/reply, queue groups. JetStream provides persistent streams with replay capability.

### RabbitMQ

Full-featured broker with routing, dead letter queues, and management UI. Use when complex routing rules and enterprise reliability guarantees matter.

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
```

### Kafka

Distributed event streaming platform, massive throughput. Overkill for homelab; use only at scale.

## Notification Pipelines

### Self-Hosted Notification Services

**Ntfy:** Simple HTTP pub/sub. Send via curl, receive in app or browser.

```bash
curl -d "Backup complete" ntfy.example.com/backups
curl -d "Error: disk full" -H "Priority: high" ntfy.example.com/alerts
```

Docker: `docker run -d -p 80:80 binwiederhier/ntfy serve`.

**Gotify:** Self-hosted push notifications with web UI and API.

**Apprise:** Unified notification library supporting 80+ services from one API:

```python
from apprise import Apprise
apobj = Apprise()
apobj.add('discord://webhook_id/webhook_token')
apobj.add('slack://token_a/token_b/token_c')
apobj.add('tgram://bottoken/chatid')
apobj.notify(body='Alert: disk full', title='System')
```

### Chat Platform Integration

**Discord webhooks:**
```bash
curl -H "Content-Type: application/json" \
  -d '{"content":"Alert: disk full","username":"Bot"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

**Slack webhooks:** Same pattern, different payload format:
```bash
curl -X POST -H 'Content-type: application/json' \
  -d '{"text":"Alert: disk full"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Telegram bot:** Create via @BotFather, send via:
```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d chat_id=<CHAT_ID> -d text="Alert: disk full"
```

### Email Notifications

Configure services to send via SMTP relay (your email provider). For self-hosted mail: deploy Mailu, Postal, or Mailcow (Docker stacks).

Use transactional email APIs (SendGrid, Mailgun, SES) for reliable delivery at scale.

### Notification Routing

```
Event → Router → Priority Check
  ├─ Critical: Discord + Email + Push
  ├─ Warning: Discord only
  └─ Info: Log only
```

## Reverse Proxy & Service Discovery

### Traefik

Auto-discovers services via Docker labels. No config files per service.

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`app.example.com`)"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

Automatic HTTPS with Let's Encrypt. Dashboard monitors routes and services.

### Nginx Proxy Manager

Web UI for reverse proxy management. Easier than raw nginx config. Let's Encrypt and access list integration built-in.

### Cloudflare Tunnels

Expose local services without opening ports or static IP:

```bash
cloudflared tunnel create myservice
cloudflared tunnel route dns myservice myservice.example.com
cloudflared tunnel run myservice
```

Zero-trust access via Cloudflare Access for authentication in front of tunnels.

## Health Monitoring

### Uptime Kuma

Self-hosted uptime monitor with public status pages. Supports HTTP, TCP, ping, DNS, and Docker container status checks.

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    ports:
      - "3001:3001"
    volumes:
      - uptime_data:/app/data
```

Integrates with 90+ notification services.

### Health Check Pattern

Every service exposes `/health` endpoint returning 200 (healthy) or 503 (unhealthy). Include dependency status (database, cache, queue).

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Monitoring Stack

- **Prometheus:** metrics collection (scrapes `/metrics` endpoints)
- **Grafana:** visualization dashboards
- **Loki:** log aggregation (pairs with Grafana)
- **Node Exporter:** system metrics (CPU, memory, disk, network)

## Common Integration Patterns

### Event-Driven Architecture

```
Service A → Event (Redis/MQTT/webhook) → Service B processes
```

Loose coupling: services don't know about each other. Accept eventual consistency (data slightly stale across services). Make consumers idempotent (handle duplicate events gracefully).

### Polling vs Webhooks vs Streaming

- **Polling:** check periodically via cron. Simple, works everywhere. Wastes resources.
- **Webhooks:** server pushes when event occurs. Efficient, real-time. Requires exposed endpoint.
- **Streaming:** persistent connection (WebSocket, SSE, MQTT). Best for real-time.

**Preference:** streaming > webhooks > polling.

### Data Transformation

ETL: extract from source, transform (reshape fields, filter, aggregate), load to destination.

```python
import json
data = json.loads(input_data)
transformed = {
    'id': data['user_id'],
    'name': f"{data['first']} {data['last']}",
    'created': data['timestamp'][:10]  # date only
}
```

Always validate transformed data before loading (schema validation, type checks).

### Service-to-Service Authentication

- **Internal services:** mutual TLS or shared secrets
- **API keys:** rotated regularly, scoped to minimum permissions
- **Service accounts:** dedicated credentials per service, not shared human accounts
- **Secret injection:** environment variables, Docker secrets, or Vault

## Cron & Scheduled Tasks

Cron expressions: `minute hour day month weekday`. Example: `0 */6 * * *` = every 6 hours.

```bash
# In Docker container or on host
0 2 * * * /usr/local/bin/backup.sh && curl https://healthchecks.io/ping/uuid

# Systemd timer (better logging, dependency management)
[Timer]
OnCalendar=*-*-* 02:00:00
```

Ping Healthchecks.io at end of job — if ping is missed, alert fires.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not received | Check firewall, verify URL reachable from sender, inspect server logs |
| Queue messages stuck | Check consumer health, inspect dead letter queue, verify message format |
| Notification not sent | Verify webhook URL/credentials, check rate limits, inspect service logs |
| Reverse proxy 502/504 | Backend down or slow, check container health, verify port mapping |
| Service can't reach another | Use container names (same network), check DNS, verify ports exposed |
| Cron job not running | Verify syntax (crontab.guru), check timezone, confirm cron daemon running |

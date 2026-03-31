---
name: observability-sre
description: "Use this skill whenever the user wants to monitor, observe, alert on, or improve the reliability of systems and services. Triggers include: any mention of 'monitoring', 'observability', 'metrics', 'logs', 'traces', 'tracing', 'Prometheus', 'Grafana', 'Loki', 'Tempo', 'Jaeger', 'OpenTelemetry', 'OTEL', 'alert', 'alerting', 'Alertmanager', 'PagerDuty', 'on-call', 'incident', 'incident response', 'postmortem', 'SLI', 'SLO', 'SLA', 'error budget', 'uptime', 'downtime', 'availability', 'reliability', 'SRE', 'site reliability', 'dashboard', 'Grafana dashboard', 'log aggregation', 'Elasticsearch', 'Fluentd', 'Fluent Bit', 'Logstash', 'ELK', 'EFK', 'structured logging', 'log analysis', 'APM', 'application performance', 'latency', 'throughput', 'error rate', 'saturation', 'health check', 'status page', 'Uptime Kuma', 'node exporter', 'cAdvisor', 'runbook', 'toil reduction', or any request to set up monitoring, create dashboards, configure alerts, debug production issues, or improve system reliability. Also use when the user asks 'why is my service slow?', 'how do I know if something is broken?', 'set up alerts for my homelab', or wants to build any kind of observability stack. If someone mentions production issues or system health concerns, use this skill."
---

# Observability & SRE

Build observability stacks that answer "what's happening?" (metrics), "why is it happening?" (logs/traces), and "should I care?" (alerts/SLOs). Covers the three pillars, self-hosted tooling, alerting philosophy, incident response, and SRE practices.

## The Three Pillars

### Metrics: What's the Trend?
Numerical measurements over time (CPU usage, request count, error rate, queue depth). Choose between:
- **Pull model (Prometheus)**: scraper fetches `/metrics` endpoint on schedule. Why: pull is safer (firewall-friendly), scraper controls load, handles backpressure.
- **Push model (Telegraf, StatsD)**: application pushes metrics to collector. Why: better for serverless/short-lived processes, real-time visibility.

Key characteristic: low cardinality (few unique label combinations), aggregated, cheap to store and query. Use for dashboards, alerts, trends, capacity planning.

### Logs: What Happened?
Discrete events with text/structured data (request handled, error occurred, user logged in). Two styles:
- **Structured logging**: JSON format, machine-parseable, queryable fields. Production-ready. Example: `{"level":"error","service":"api","trace_id":"abc123","status":500}`
- **Unstructured**: plain text, human-readable but hard to query at scale.

Key characteristic: high cardinality, detailed, expensive to store at scale (cost-optimize via sampling and filtering). Use for debugging, audit trails, forensics, correlation.

### Traces: How Did the Request Flow?
Request lifecycle across services. One trace = one user request. Spans = individual operations (each service call is a span). Trace ID = unique identifier following request across all services.

Why traces matter: find bottlenecks fast. "Why is checkout slow?" → click trace → see database query taking 5s → fix. Use for distributed system debugging, bottleneck discovery.

---

## Metrics Stack: Prometheus + Grafana

### Prometheus Setup
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

volumes:
  prometheus_data:
```

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
  
  - job_name: 'apps'
    static_configs:
      - targets: ['app1:8080', 'app2:8080']
```

Access UI at `http://localhost:9090`. Status → Targets shows scrape health.

### Common Exporters (Why Each Exists)
- **Node Exporter** (9100): CPU, memory, disk, network for Linux hosts. Essential for infrastructure monitoring.
- **cAdvisor** (8080): container metrics (CPU, memory, network per container). Understand per-container resource usage.
- **Blackbox Exporter**: probe endpoints (HTTP, TCP, ICMP, DNS). Synthetic monitoring — verify external services are reachable.
- **SNMP Exporter**: network devices (switches, routers, UPS). Legacy infrastructure monitoring.
- **Custom /metrics**: instrument your application with Prometheus client library. App-level observability (request counts, durations, business metrics).

### Grafana: Visualization
- Pairs with Prometheus, Loki, Tempo, PostgreSQL, InfluxDB, Elasticsearch
- **Provisioning (dashboards-as-code)**: store JSON in git, auto-loaded on startup. Version control your dashboards.
- **Community dashboards**: import by ID from grafana.com (Node Exporter: 1860, Docker: 193, Prometheus: 3662)
- **Variables**: templated dashboards with dropdown selectors ($host, $service, $environment). Single dashboard works for all instances.

### PromQL: Query Language (Examples)

```promql
# CPU usage percentage
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Request rate (req/sec) — why: measure throughput
rate(http_requests_total[5m])

# Error rate percentage — why: know if service is degraded
(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100

# p95 latency in seconds — why: know user experience
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Memory usage percentage — why: capacity planning
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk space remaining percentage — why: prevent "disk full" disasters
(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

Key PromQL concepts:
- `rate(metric[5m])`: per-second change over 5 minutes (for counters)
- `avg by(label)`: aggregate across label values
- `histogram_quantile(0.95, ...)`: 95th percentile from histogram buckets
- Range: `[5m]`, `[1h]` — window for calculation

---

## Logging Stack: Loki + Grafana (or ELK)

### Loki: Why It's Lightweight
Designed to be cost-effective: **indexes labels, not content**. Query by service/job/level (low cardinality), not by searching log text (expensive). 10x less resource usage than ELK, simpler operations.

```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

volumes:
  loki_data:
```

**promtail-config.yml**:
```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets: [localhost]
        labels:
          job: syslog
          __path__: /var/log/*.log

  - job_name: docker
    static_configs:
      - targets: [localhost]
        labels:
          job: docker
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
```

### When to Use ELK Instead
ELK (Elasticsearch + Logstash + Kibana) or EFK (Fluent Bit instead of Logstash): if you need complex full-text search, heavy log analysis, or already run Elasticsearch. Trade-off: more resources, more operational overhead, but powerful search.

### Structured Logging Best Practices

```python
import structlog
logger = structlog.get_logger()

# Good: structured, queryable fields
logger.info("order_placed", order_id=12345, user_id=67, total=99.99, items=3)

# Bad: unstructured, hard to query
logger.info(f"Order {order_id} placed by user {user_id}...")

# Standard fields: timestamp, level, message, service, trace_id, request_id
# Don't log: passwords, tokens, PII (or redact before logging)
# Log levels: DEBUG (dev only), INFO (normal), WARNING (unexpected but handled), ERROR (action needed), CRITICAL (system down)
```

JSON format makes every log line machine-parseable and queryable. Include trace_id/request_id to correlate across services.

### LogQL: Query Language (Examples)

```logql
# All error logs from a specific service
{service="api"} |= "error"

# Parse JSON and filter (pipe = filter, | json = parse JSON fields)
{service="api"} | json | level="ERROR" | status >= 500

# Count errors per minute
count_over_time({service="api"} |= "error" [1m])

# Errors from specific container
{container="api"} !="200" | json | level="ERROR"
```

---

## Tracing: OpenTelemetry + Tempo

### OpenTelemetry (OTEL)
Vendor-neutral standard for instrumentation. Single SDK instruments metrics + logs + traces simultaneously. Auto-instrumentation available: instrument HTTP clients, database drivers, frameworks without code changes.

OTEL Collector: receives, processes (sample, batch, enrich), exports telemetry to backends.

### Tempo (Grafana)
Trace storage backend, integrates with Grafana. Lightweight, cost-effective (stores in object storage S3/GCS/filesystem). Click from Grafana metric → see exemplars → click → see related traces → see related logs.

### Practical Tracing Pattern

1. Application sends traces via OTEL SDK → OTEL Collector
2. Collector exports to Tempo (storage) + optional sampling (keep 1% of traces to reduce storage)
3. Grafana queries Tempo, visualizes request flow across services
4. Correlate: metric alert fires → exemplar links → trace → span with error → related logs in Loki

Why traces: "Why is checkout slow?" → trace shows database query taking 8s → fix the query.

---

## Alerting: Alert on Symptoms, Not Causes

### Philosophy
- **Alert on symptoms**: users affected, money lost, data at risk. NOT "CPU is high" (CPU high doesn't mean users suffer).
- **Every alert must be actionable**: if there's nothing to do, it's a metric, not an alert.
- **Reduce noise**: one meaningful alert > ten noisy ones. Alert fatigue kills response time (people stop reading them).
- **Severity levels**: critical (page NOW), warning (investigate work hours), info (dashboard only).

### Alertmanager Config

```yaml
# alertmanager.yml
route:
  receiver: 'default'
  group_wait: 30s        # Wait 30s for related alerts before sending (batch)
  group_interval: 5m     # Resend group every 5m
  repeat_interval: 4h    # Repeat after 4 hours if still firing
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://ntfy.local/alerts'  # Self-hosted notification
  - name: 'slack'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK_URL>'
        channel: '#alerts'
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_KEY>'
        severity: 'error'
```

### Prometheus Alert Rules

```yaml
groups:
  - name: infrastructure
    rules:
      - alert: HighCPU
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 5m  # Must be true 5+ minutes (prevents flapping)
        labels:
          severity: warning
        annotations:
          summary: "High CPU on {{ $labels.instance }}"
          description: "CPU > 90% for 5m (current: {{ $value }}%)"
          runbook: "https://wiki/runbooks#HighCPU"

      - alert: DiskSpaceCritical
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disk space < 10% on {{ $labels.instance }}"
          runbook: "https://wiki/runbooks#DiskSpace"

      - alert: ServiceDown
        expr: up{job="api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API service down on {{ $labels.instance }}"
```

Key concepts:
- `for: 5m`: alert fires only if condition true for 5+ minutes (prevents flapping)
- `labels`: route to correct receiver (severity, team)
- `annotations`: details shown to on-call (summary, description, runbook link, value)

### Essential Alerts for Any Homelab/Production
- **Disk < 10%** (critical), **< 20%** (warning) → fills up = outage
- **Container restart count > 3 in 15m** → app crashing repeatedly
- **Service endpoint down** (blackbox probe failing) → users affected
- **Memory > 90% for 10m** → potential OOM kill
- **SSL cert expiring in 7 days** → service unavailable after expiry
- **Backup job failed or missed** → data loss risk
- **ZFS/RAID degraded** → single disk failure = data loss

---

## SLIs, SLOs, Error Budgets

### Definitions
- **SLI (Service Level Indicator)**: the metric you measure (availability %, latency p99, error rate)
- **SLO (Service Level Objective)**: target for that metric (99.9% availability, p99 < 500ms)
- **SLA (Service Level Agreement)**: contractual commitment (breach = penalties)
- **Error Budget**: failure permitted by SLO (99.9% = 8.76 hours downtime/year)

Why this matters: SLO guides deployment velocity. If you have 50 hours/year error budget, you can deploy knowing you have margin.

### Common SLIs & How to Measure
- **Availability**: `(successful_requests / total_requests) * 100`
- **Latency**: response time at p50, p95, p99 (p99 = 99% of requests faster than this)
- **Error rate**: `(failed_requests / total_requests) * 100`
- **Throughput**: successful requests per second

### Setting SLOs (Right)
1. Measure current baseline (what do you actually achieve today?)
2. Set SLO slightly below baseline (gives room for incidents)
3. 99.9% (3 nines) is good starting target: 8.76 hours/year downtime, 30 minutes/month
4. Don't target 100% — it's impossible, you'd never deploy

Trade-off: higher SLO = more operational burden (more testing, fewer deployments). Choose wisely.

---

## Incident Response: From Alert to Fix to Prevention

### The Process
1. **Detect**: alert fires or user reports issue
2. **Triage**: impact assessment (how many users? data at risk?)
3. **Communicate**: update status page, notify stakeholders
4. **Mitigate**: restore service FIRST (rollback, restart, scale), investigate later
5. **Resolve**: fix underlying issue
6. **Postmortem**: blameless analysis — what happened, why, how to prevent

Why order matters: mitigate before investigating. User impact > root cause analysis. You can investigate while service is up.

### Runbooks: Pre-Written Playbooks
Store in git alongside alerting rules. Structure:
```
# Alert: HighCPU

**Impact**: Slow responses, user requests timing out

**Diagnosis**:
- `top` on host to see which process consuming CPU
- Check if recently deployed code introduced tight loop
- Check if DDoS or legitimate traffic spike

**Remediation**:
- Quick: restart process/container
- Medium: scale horizontally (add instances)
- If code issue: rollback to previous version

**Escalation**: page database team if query optimization needed
```

Link runbook URL in alert annotations so on-call finds it immediately. Automate what you can (curl to drain/scale), document what you can't.

### Status Pages
Tools: Uptime Kuma (self-hosted), Statuspage.io, Instatus
Display: service health (green/yellow/red), incident history, maintenance windows
Why: users see status, get estimated time to resolution, don't spam support

---

## Full Observability Stack (Docker Compose)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus/:/etc/prometheus/
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml

  node-exporter:
    image: prom/node-exporter:latest
    ports: ["9100:9100"]
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

  alertmanager:
    image: prom/alertmanager:latest
    ports: ["9093:9093"]
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
  alertmanager_data:
```

Start: `docker-compose up -d`
- Grafana: http://localhost:3000 (add Prometheus, Loki data sources)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

---

## Troubleshooting Reference

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| No metrics | Check Prometheus Status → Targets (red = scrape failing) | Verify `/metrics` endpoint reachable, check firewall |
| Dashboard empty | Check time range (top right), verify PromQL syntax | Test query in Prometheus → Graphs first |
| Alerts not firing | Check alert expr in Prometheus UI (Status → Rules) | Verify Alertmanager running, check routing rules |
| Log volume high | Check Promtail job configs | Increase log level to WARNING, add sampling, filter sources |
| Traces missing spans | Check OTEL SDK initialized in all services | Verify collector endpoint reachable, check pipeline config |
| Grafana slow | Reduce query time range, use recording rules | Enable query caching, increase panel refresh interval |

---

## Key Takeaways

- **Metrics + Logs + Traces** answer different questions. All three together = complete visibility.
- **SLOs guide velocity**: high SLO = low change rate, low SLO = fast deployments.
- **Alert on symptoms** (users slow, errors rising), not infrastructure (CPU high).
- **Runbooks + postmortems** prevent repeated incidents.
- **Start simple**: Prometheus + Grafana + Loki. Add Tempo/Jaeger only when debugging distributed systems.
- **Automate recovery**: alerts → pagerduty → runbook → automated remediation where possible.

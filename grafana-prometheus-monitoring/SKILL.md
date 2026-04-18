---
name: grafana-prometheus-monitoring
description: "Use this when: set up Grafana dashboards, configure Prometheus scraping, write recording rules, configure alerting, monitoring is broken, dashboards are wrong, cardinality is exploding, set up SLOs, configure Alertmanager, GPU monitoring, AI training metrics, model inference monitoring, LiteLLM metrics, vLLM metrics, Ollama metrics, Qdrant health, vector DB monitoring, DCGM exporter, dashboards as code, provision Grafana without clicking, Grafana API, Grizzly, Grafonnet, Terraform grafana provider, kube-prometheus-stack, multi-burn-rate alerts, MWMBR, RED method, USE method, node exporter, cadvisor, blackbox exporter, Prometheus federation, remote write, high availability, Loki, Tempo, Mimir, AI workflow monitoring, training job metrics, inference monitoring, model serving SLO, drift detection, pushgateway"
---

# Grafana + Prometheus Monitoring

## Identity

You are a monitoring and observability engineer. Every configuration you produce is code-first:
no manual UI clicks, no one-off Grafana edits, no scrape targets added by hand. Dashboards live
in git. Rules live in files. Datasources are provisioned. The Grafana UI is read-only by
convention — `allowUiUpdates: false` is always set.

You produce working config blocks, deploy commands, and provisioning files. Not instructions to
click buttons.

---

## Template Variables

All configs use `<PLACEHOLDER>` for values the operator must supply. Collect these before
generating any config. When using Docker Compose, these map to a `.env` file.

```bash
# .env.example — copy to .env and fill in before running
CLUSTER_NAME=my-cluster           # logical cluster label on all metrics
ENVIRONMENT=production            # e.g. production, staging, homelab
GRAFANA_ADMIN_PASSWORD=changeme
GRAFANA_API_TOKEN=                # service account token for API/CI deploys
PROMETHEUS_RETENTION=90d
REMOTE_WRITE_URL=                 # Mimir/Thanos endpoint, blank = local only

# Inference proxy (LiteLLM / OpenAI-compatible gateway)
INFERENCE_HOST=litellm            # Docker service name or hostname
INFERENCE_PORT=8000               # LiteLLM default 8000, varies by deployment

# Vector DB
VECTOR_DB_HOST=qdrant             # Docker service name or hostname
VECTOR_DB_PORT=6333               # Qdrant default

# GPU nodes (add one block per node)
GPU_NODE_1_HOST=<gpu-node-1-ip>
GPU_NODE_1_NAME=gpu-node-1

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
PAGERDUTY_KEY=                    # PagerDuty routing key for critical alerts
RUNBOOK_BASE_URL=https://wiki.example.com/runbooks
```

---

## Stack Defaults

| Layer | Tool | Why |
|-------|------|-----|
| Metrics store | Prometheus (pull model) | Battle-tested, PromQL, recording rules, 15s scrape |
| Long-term storage | Grafana Mimir or Thanos | Object storage backend, horizontal scale, dedup |
| Visualization | Grafana (provisioned from git) | Variables, unified alerting, exemplar links |
| Logs | Loki + Promtail / Alloy | Label-indexed; 10x cheaper than ELK for structured logs |
| Traces | Tempo + OTEL Collector | Vendor-neutral; links to metrics and logs via exemplars |
| Alerting | Prometheus Alertmanager | group/route/silence; critical→PagerDuty, warning→Slack |
| GPU metrics (NVIDIA) | DCGM Exporter | CUDA-aware util, memory, power, NVLink, MIG |
| GPU metrics (AMD) | amd-smi-exporter or ROCm SMI | Equivalent coverage for AMD/ROCm stacks |
| AI inference | vLLM /metrics, LiteLLM /metrics, Ollama /metrics, Triton /metrics | Native Prometheus endpoints |
| Training metrics | Prometheus Pushgateway | Push from batch job; scrape by Prometheus |
| Synthetic / probes | Blackbox Exporter | HTTP/TCP health, TLS cert expiry |
| Provisioning | Grafana provisioning YAMLs + Grafana API | Zero UI clicks; idempotent; git-tracked |
| Dashboards-as-code | Grafonnet (jsonnet) or Grizzly YAML | Programmatic; CI/CD deployable |
| IaC | Terraform grafana provider v3 | Folders, datasources, dashboards, alert policies |

---

## Decision Framework

### Provisioning Method (zero manual config — choose one)

- If stack is Docker Compose → mount provisioning YAMLs at `/etc/grafana/provisioning/`; dashboard JSONs at `/var/lib/grafana/dashboards/`
- If Kubernetes → ConfigMap-mounted provisioning YAMLs + kube-prometheus-stack Helm chart
- If CI/CD pipeline deploys dashboards → Grizzly (`grr apply`) or Grafana HTTP API (`POST /api/dashboards/db`)
- If full IaC required → Terraform `grafana_dashboard`, `grafana_data_source`, `grafana_folder` resources
- Default → Docker Compose provisioning YAMLs; graduate to Terraform when managing > 3 environments

### Metrics Collection

- If host / bare-metal VM → `node_exporter` on :9100; file_sd_configs for zero-restart target addition
- If containers / Docker → `cAdvisor` on :8080; mount Docker socket read-only
- If NVIDIA GPU → `dcgm-exporter` on :9400; requires nvidia-container-runtime
- If AMD GPU → `amd-smi-exporter` on :2021; requires ROCm driver on host
- If AI inference service → scrape native `/metrics` endpoint; port varies by server (see AI section)
- If training job (batch, exits after run) → push metrics to Pushgateway; scrape Pushgateway
- If external URL / certificate → Blackbox Exporter HTTP/TLS probe
- If vector DB (Qdrant, Weaviate, Milvus) → scrape native metrics endpoint (see AI section)
- Default → node_exporter + cAdvisor + blackbox; layer GPU and AI exporters as needed

### Alert Design

- If alert fires > 5×/day without a corresponding incident → raise `for:` duration or delete it; it's a metric, not an alert
- If alerting on resource saturation (CPU%, RAM%, GPU%) → replace with user-facing SLO signal first
- If service has a defined SLO → use multi-window multi-burn-rate (MWMBR: 1h/5m fast + 6h/30m slow)
- If no SLO defined yet → alert on: error rate > 1%, p99 latency > threshold, availability < 99.9%
- If training job → alert on: job failure, loss divergence (NaN/plateau), OOM, GPU util < 10% for > 10m
- If inference service → alert on: p99 > 2s, error rate > 0.5%, token queue depth > limit
- Every alert MUST carry `runbook_url:` annotation — no runbook = no ship

### Histogram vs Summary

- Default → histogram with explicit buckets matching expected latency range
- Never use summary when you need to aggregate quantiles across multiple instances
- Native histograms (Prometheus 2.40+) preferred over classic bucket histograms when available
- Web service buckets: `[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]`
- AI inference buckets (ms): `[10, 25, 50, 100, 250, 500, 1000, 2000, 5000]`

### Cardinality Control

- Never use `user_id`, `request_id`, `session_id`, `trace_id` as Prometheus label values
- Cardinality budget: < 10,000 series per scrape job; > 100,000 = production incident risk
- If an exporter produces high-cardinality labels → use `metric_relabel_configs: [action: labeldrop]`
- Use `topk(10, ...)` in dashboards for unbounded dimensions (model name, endpoint path)
- Run `tsdb analyze` periodically to find cardinality hotspots before they OOM

### Long-term Storage / HA

- Single Prometheus, < 90d retention → local storage sufficient; add `remote_write` for off-host backup
- Multi-DC or > 6 months retention → Thanos with object store or Grafana Mimir
- HA: run 2 Prometheus replicas with identical configs + `--storage.tsdb.allow-overlapping-blocks`; deduplicate at Thanos Querier or Mimir query-frontend
- Alertmanager HA: 3 replicas minimum with gossip (`--cluster.peer`); route critical to PagerDuty

---

## Dashboard Provisioning (Code-First Patterns)

### Pattern 1 — Docker Compose + Provisioning YAMLs (default)

```yaml
# docker-compose.yml — monitoring stack
# Requires: .env file with variables from .env.example
services:
  grafana:
    image: grafana/grafana:11.0.0
    volumes:
      - ./provisioning:/etc/grafana/provisioning:ro
      - ./dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: /var/lib/grafana/dashboards/overview/home.json
      GF_AUTH_ANONYMOUS_ENABLED: "false"
    ports: ["3000:3000"]
    networks: [monitoring]
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.53.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./rules:/etc/prometheus/rules:ro
      - ./targets:/etc/prometheus/targets:ro
      - prometheus_data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-90d}
      - --storage.tsdb.allow-overlapping-blocks
      - --web.enable-lifecycle        # enables POST /-/reload
      - --web.enable-admin-api
    ports: ["9090:9090"]
    networks: [monitoring]
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.27.0
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    ports: ["9093:9093"]
    networks: [monitoring]
    restart: unless-stopped

  pushgateway:
    image: prom/pushgateway:v1.9.0
    ports: ["9091:9091"]
    networks: [monitoring]
    restart: unless-stopped

  blackbox-exporter:
    image: prom/blackbox-exporter:v0.25.0
    volumes:
      - ./blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    ports: ["9115:9115"]
    networks: [monitoring]
    restart: unless-stopped

volumes:
  grafana_data:
  prometheus_data:

networks:
  monitoring:
    enable_ipv6: false
```

```yaml
# provisioning/datasources/datasources.yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    editable: false
    jsonData:
      derivedFields:
        - matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "${__value.raw}"
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    uid: tempo
    url: http://tempo:3200
    editable: false
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
      tracesToMetrics:
        datasourceUid: prometheus
      serviceMap:
        datasourceUid: prometheus
```

```yaml
# provisioning/dashboards/default.yaml
apiVersion: 1
providers:
  - name: default
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false       # UI edits silently discarded — git is source of truth
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true  # subfolder name = Grafana folder name
```

### Pattern 2 — Grafana HTTP API (idempotent import)

```bash
# Import or overwrite a dashboard — safe to re-run in CI
GRAFANA_URL=http://<GRAFANA_HOST>:3000
GRAFANA_TOKEN=${GRAFANA_API_TOKEN}

curl -sf -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  "${GRAFANA_URL}/api/dashboards/db" \
  -d @- <<EOF
{
  "dashboard": $(cat dashboards/node-overview.json),
  "folderId": 0,
  "overwrite": true,
  "message": "ci:$(git rev-parse --short HEAD)"
}
EOF

# Provision datasource via API
curl -sf -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  "${GRAFANA_URL}/api/datasources" \
  -d '{
    "name":"Prometheus","type":"prometheus",
    "url":"http://<PROMETHEUS_HOST>:9090","access":"proxy","isDefault":true
  }'

# Hot-reload Prometheus config (no restart required)
curl -sf -X POST http://<PROMETHEUS_HOST>:9090/-/reload
```

### Pattern 3 — Grizzly CLI Deploy

```bash
# Install
go install github.com/grafana/grizzly/cmd/grr@latest

export GRAFANA_URL=http://<GRAFANA_HOST>:3000
export GRAFANA_TOKEN=${GRAFANA_API_TOKEN}

grr apply monitoring/            # deploy all resources
grr diff  monitoring/            # preview changes before apply
grr pull  Dashboard/uid-here     # pull existing UI dashboard to code
```

```yaml
# monitoring/dashboards/node-overview.yaml (Grizzly format)
apiVersion: grizzly.grafana.com/v1alpha1
kind: Dashboard
metadata:
  name: node-overview
  folder: Infrastructure
spec:
  title: Node Overview
  uid: node-overview
  panels: []   # paste full Grafana JSON panels array here
```

### Pattern 4 — Terraform grafana Provider

```hcl
# variables.tf
variable "grafana_url"           { type = string }
variable "grafana_service_token" { type = string, sensitive = true }
variable "prometheus_url"        { type = string, default = "http://prometheus:9090" }

terraform {
  required_providers {
    grafana = { source = "grafana/grafana", version = "~> 3.0" }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_service_token
}

resource "grafana_folder" "ai_monitoring" {
  title = "AI Monitoring"
}

resource "grafana_dashboard" "inference" {
  folder      = grafana_folder.ai_monitoring.id
  config_json = file("${path.module}/dashboards/inference-overview.json")
  overwrite   = true
  message     = "terraform apply"
}

resource "grafana_data_source" "prometheus" {
  type       = "prometheus"
  name       = "Prometheus"
  url        = var.prometheus_url
  is_default = true
  json_data_encoded = jsonencode({
    timeInterval = "15s"
    exemplarTraceIdDestinations = [
      { name = "traceID", datasourceUid = "tempo" }
    ]
  })
}
```

---

## Prometheus Configuration

### prometheus.yml — File-SD (add targets without restarting Prometheus)

```yaml
global:
  scrape_interval:     15s
  evaluation_interval: 15s
  external_labels:
    cluster: ${CLUSTER_NAME}      # set in environment or .env
    env:     ${ENVIRONMENT}

rule_files:
  - /etc/prometheus/rules/*.yaml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

# Optional: remote write to Mimir, Thanos, or Grafana Cloud
# Remove or comment out if running standalone
remote_write:
  - url: ${REMOTE_WRITE_URL}      # e.g. http://mimir:9009/api/v1/push
    queue_config:
      max_samples_per_send: 10000
      batch_send_deadline: 5s

scrape_configs:

  # ── Infrastructure ──────────────────────────────────────────────────────────

  # Hosts — drop JSON files into /targets/nodes/ to add targets; no restart
  - job_name: node
    file_sd_configs:
      - files: ["/etc/prometheus/targets/nodes/*.json"]
        refresh_interval: 30s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance

  # Containers
  - job_name: cadvisor
    file_sd_configs:
      - files: ["/etc/prometheus/targets/cadvisor/*.json"]
        refresh_interval: 30s

  # Blackbox / synthetic probes
  - job_name: blackbox_http
    metrics_path: /probe
    params:
      module: [http_2xx]
    file_sd_configs:
      - files: ["/etc/prometheus/targets/blackbox/*.json"]
        refresh_interval: 60s
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # ── AI / Inference ──────────────────────────────────────────────────────────

  # AI inference proxy — LiteLLM, vLLM, or any OpenAI-compatible gateway
  # Port varies: LiteLLM 8000, vLLM 8000, Ollama 11434 (set in target file)
  - job_name: ai_inference
    file_sd_configs:
      - files: ["/etc/prometheus/targets/ai_inference/*.json"]
        refresh_interval: 30s
    metric_relabel_configs:
      # Drop high-cardinality per-request labels if present
      - regex: "request_id|session_id|user_id|trace_id"
        action: labeldrop

  # Vector DB — Qdrant, Weaviate, Milvus (set correct port in target file)
  - job_name: vector_db
    file_sd_configs:
      - files: ["/etc/prometheus/targets/vector_db/*.json"]
        refresh_interval: 30s

  # Training Pushgateway
  - job_name: pushgateway
    honor_labels: true             # preserve job/instance from pushed metrics
    static_configs:
      - targets: ["pushgateway:9091"]

  # ── GPU nodes ───────────────────────────────────────────────────────────────
  # Drop one JSON file per GPU node into /targets/gpu/
  - job_name: dcgm
    file_sd_configs:
      - files: ["/etc/prometheus/targets/gpu/*.json"]
        refresh_interval: 30s
    metric_relabel_configs:
      # Normalise GPU index label across DCGM versions
      - source_labels: [gpu]
        target_label: gpu_index
```

### File-SD Target Templates

```json
// /etc/prometheus/targets/nodes/node-1.json
[{
  "targets": ["<NODE_HOST_OR_IP>:9100"],
  "labels": { "job": "node", "instance": "<NODE_NAME>", "role": "<ROLE>" }
}]
```

```json
// /etc/prometheus/targets/gpu/gpu-node-1.json
[{
  "targets": ["<GPU_NODE_HOST_OR_IP>:9400"],
  "labels": {
    "job": "dcgm",
    "instance": "<GPU_NODE_NAME>",
    "gpu_vendor": "nvidia",
    "gpu_model": "<GPU_MODEL>"
  }
}]
```

```json
// /etc/prometheus/targets/ai_inference/litellm.json
[{
  "targets": ["<INFERENCE_HOST>:<INFERENCE_PORT>"],
  "labels": {
    "job": "ai_inference",
    "instance": "<INFERENCE_HOST>",
    "server_type": "litellm"
  }
}]
```

```json
// /etc/prometheus/targets/ai_inference/vllm.json
[{
  "targets": ["<VLLM_HOST>:8000"],
  "labels": {
    "job": "ai_inference",
    "instance": "<VLLM_HOST>",
    "server_type": "vllm",
    "model": "<MODEL_NAME>"
  }
}]
```

```json
// /etc/prometheus/targets/ai_inference/ollama.json
[{
  "targets": ["<OLLAMA_HOST>:11434"],
  "labels": {
    "job": "ai_inference",
    "instance": "<OLLAMA_HOST>",
    "server_type": "ollama"
  }
}]
```

```json
// /etc/prometheus/targets/vector_db/qdrant.json
[{
  "targets": ["<QDRANT_HOST>:6333"],
  "labels": { "job": "vector_db", "instance": "<QDRANT_HOST>", "db_type": "qdrant" }
}]
```

---

## Recording Rules (naming: `level:metric:operations`)

```yaml
# /etc/prometheus/rules/ai_recording.yaml
groups:
  - name: ai_inference_recording
    interval: 30s
    rules:

      # ── LiteLLM / OpenAI-proxy metrics ──────────────────────────────────────
      # Adjust metric names if using vLLM or another server (see AI section)

      - record: model:http_requests:rate5m
        expr: sum by (model, status_code) (rate(litellm_requests_metric_total[5m]))

      - record: model:http_errors:rate5m
        expr: |
          sum by (model) (rate(litellm_requests_metric_total{status_code=~"5.."}[5m]))
          / sum by (model) (rate(litellm_requests_metric_total[5m]))

      - record: model:inference_latency_seconds:p99_5m
        expr: |
          histogram_quantile(0.99,
            sum by (model, le) (rate(litellm_request_duration_seconds_bucket[5m])))

      - record: model:tokens_per_second:rate5m
        expr: sum by (model) (rate(litellm_total_tokens[5m]))

      # SLI recording rules (required by MWMBR alerts below)
      - record: job:slo_error_rate:rate5m
        expr: |
          1 - (
            sum by (job) (rate(litellm_requests_metric_total{status_code=~"2.."}[5m]))
            / sum by (job) (rate(litellm_requests_metric_total[5m]))
          )
      - record: job:slo_error_rate:rate1h
        expr: |
          1 - (
            sum by (job) (rate(litellm_requests_metric_total{status_code=~"2.."}[1h]))
            / sum by (job) (rate(litellm_requests_metric_total[1h]))
          )
      - record: job:slo_error_rate:rate6h
        expr: |
          1 - (
            sum by (job) (rate(litellm_requests_metric_total{status_code=~"2.."}[6h]))
            / sum by (job) (rate(litellm_requests_metric_total[6h]))
          )

  - name: gpu_recording
    interval: 30s
    rules:
      - record: node:gpu_utilization:avg5m
        expr: avg by (instance, gpu_index) (DCGM_FI_DEV_GPU_UTIL)

      - record: node:gpu_memory_used_ratio:avg5m
        expr: |
          avg by (instance, gpu_index) (DCGM_FI_DEV_FB_USED)
          / (avg by (instance, gpu_index) (DCGM_FI_DEV_FB_USED)
           + avg by (instance, gpu_index) (DCGM_FI_DEV_FB_FREE))

      - record: node:gpu_power_watts:avg5m
        expr: avg by (instance, gpu_index) (DCGM_FI_DEV_POWER_USAGE)

  - name: training_recording
    interval: 60s
    rules:
      - record: training_job:last_push_age_seconds:gauge
        expr: time() - push_time_seconds{job="pushgateway"}
```

---

## Alerting Rules

```yaml
# /etc/prometheus/rules/ai_alerts.yaml
# Replace ${RUNBOOK_BASE_URL} with your actual wiki/runbook base URL
groups:
  - name: ai_inference_alerts
    rules:
      - alert: InferenceHighErrorRate
        expr: model:http_errors:rate5m > 0.05
        for: 5m
        labels: { severity: warning, team: ai }
        annotations:
          summary: "{{ $labels.model }} error rate {{ $value | humanizePercentage }}"
          runbook_url: "${RUNBOOK_BASE_URL}/inference-errors"

      - alert: InferenceHighLatencyP99
        expr: model:inference_latency_seconds:p99_5m > 2.0
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "{{ $labels.model }} p99 {{ $value | humanizeDuration }}"
          runbook_url: "${RUNBOOK_BASE_URL}/inference-latency"

      - alert: InferenceServiceDown
        expr: up{job="ai_inference"} == 0
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "Inference service {{ $labels.instance }} is down"
          runbook_url: "${RUNBOOK_BASE_URL}/inference-down"

  - name: gpu_alerts
    rules:
      - alert: GPUHighTemperature
        expr: DCGM_FI_DEV_GPU_TEMP > 85
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "GPU {{ $labels.gpu_index }} on {{ $labels.instance }} at {{ $value }}°C"
          runbook_url: "${RUNBOOK_BASE_URL}/gpu-thermal"

      - alert: GPUMemoryNearFull
        expr: node:gpu_memory_used_ratio:avg5m > 0.92
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "GPU {{ $labels.gpu_index }} on {{ $labels.instance }} memory {{ $value | humanizePercentage }}"
          runbook_url: "${RUNBOOK_BASE_URL}/gpu-memory"

      - alert: GPUUnderutilizedDuringTraining
        expr: |
          node:gpu_utilization:avg5m < 10
          and on (instance) training_job:last_push_age_seconds:gauge < 300
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "GPU {{ $labels.gpu_index }} on {{ $labels.instance }} underutilized during active training"
          runbook_url: "${RUNBOOK_BASE_URL}/gpu-underutilized"

  - name: training_alerts
    rules:
      - alert: TrainingJobStalled
        expr: training_job:last_push_age_seconds:gauge > 3600
        for: 0m
        labels: { severity: critical }
        annotations:
          summary: "Training job {{ $labels.exported_job }} has not pushed metrics in 1h"
          runbook_url: "${RUNBOOK_BASE_URL}/training-stalled"

      - alert: TrainingLossNaN
        expr: training_loss{phase="train"} != training_loss{phase="train"}
        for: 0m
        labels: { severity: critical }
        annotations:
          summary: "Training loss is NaN for job {{ $labels.exported_job }}"
          runbook_url: "${RUNBOOK_BASE_URL}/training-nan"

  - name: slo_mwmbr
    # Multi-window multi-burn-rate (MWMBR) — SLO: 99.9% (adjust 0.001 for your target)
    # 99.9% → 0.001 error budget | 99.5% → 0.005 | 99.0% → 0.010
    rules:
      - alert: SLOBurnRateFast          # 14.4× burn → exhausts budget in 1h
        expr: |
          (job:slo_error_rate:rate1h > (14.4 * 0.001))
          and
          (job:slo_error_rate:rate5m > (14.4 * 0.001))
        for: 2m
        labels: { severity: critical, window: fast }
        annotations:
          summary: "{{ $labels.job }} fast burn: {{ $value | humanizePercentage }} error rate"
          runbook_url: "${RUNBOOK_BASE_URL}/slo-burn"

      - alert: SLOBurnRateSlow           # 6× burn → exhausts budget in 6h
        expr: |
          (job:slo_error_rate:rate6h > (6 * 0.001))
          and
          (job:slo_error_rate:rate30m > (6 * 0.001))
        for: 15m
        labels: { severity: warning, window: slow }
        annotations:
          summary: "{{ $labels.job }} slow burn: {{ $value | humanizePercentage }} error rate"
          runbook_url: "${RUNBOOK_BASE_URL}/slo-burn"
```

---

## Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: ${SLACK_WEBHOOK_URL}

route:
  group_by: [alertname, cluster, service]
  group_wait:      30s
  group_interval:  5m
  repeat_interval: 4h
  receiver: slack-warning
  routes:
    - match: { severity: critical }
      receiver: pagerduty-critical
      continue: false
    - match: { severity: warning }
      receiver: slack-warning

receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - routing_key: ${PAGERDUTY_KEY}
        description: "{{ .CommonAnnotations.summary }}"
        details:
          runbook: "{{ .CommonAnnotations.runbook_url }}"

  - name: slack-warning
    slack_configs:
      - channel: "#alerts"
        title: "[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}"
        text: "{{ .CommonAnnotations.summary }}\nRunbook: {{ .CommonAnnotations.runbook_url }}"

inhibit_rules:
  - source_match:   { severity: critical }
    target_match:   { severity: warning }
    equal: [alertname, cluster, service]
```

---

## AI / ML Monitoring

### GPU Exporters

**NVIDIA — DCGM Exporter**

```yaml
# docker-compose addition (runs on each GPU host, or as a separate stack)
services:
  dcgm-exporter:
    image: nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.0-ubuntu22.04
    runtime: nvidia
    environment:
      NVIDIA_VISIBLE_DEVICES: all
    cap_add: [SYS_ADMIN]
    ports: ["9400:9400"]
    restart: unless-stopped
    networks: [monitoring]
```

**AMD — ROCm SMI Exporter**

```yaml
services:
  amd-smi-exporter:
    image: rocm/amd-smi-exporter:latest
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    ports: ["2021:2021"]
    restart: unless-stopped
    networks: [monitoring]
```

Key NVIDIA DCGM metrics:

| Metric | Meaning | Typical Alert |
|--------|---------|---------------|
| `DCGM_FI_DEV_GPU_UTIL` | Compute utilization % | < 10% during active training |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth % | — |
| `DCGM_FI_DEV_FB_USED` | VRAM used (MiB) | > 92% of (FB_USED+FB_FREE) |
| `DCGM_FI_DEV_FB_FREE` | VRAM free (MiB) | — |
| `DCGM_FI_DEV_GPU_TEMP` | Temperature °C | > 85°C |
| `DCGM_FI_DEV_POWER_USAGE` | Power draw (W) | > TDP × 0.95 |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | NVLink bytes/s | — |
| `DCGM_FI_PROF_TENSOR_ACTIVE` | Tensor core utilization | — |

### AI Inference Servers — Native Metrics Endpoints

| Server | Default Port | Metrics Path | Notes |
|--------|-------------|--------------|-------|
| LiteLLM | 8000 | `/metrics` | Enable: `general_settings.enable_prometheus: true` |
| vLLM | 8000 | `/metrics` | Always on; set `--host 0.0.0.0` |
| Ollama | 11434 | `/metrics` | Available in Ollama ≥ 0.1.38 |
| Triton Inference Server | 8002 | `/metrics` | Set `--allow-metrics true` |
| Ray Serve | 8265 | `/metrics` | Requires `ray[default]` metrics plugin |

**Enable LiteLLM Prometheus endpoint:**
```yaml
# config.yaml
general_settings:
  enable_prometheus: true
  prometheus_port: 8000   # same port as API by default
```

Key LiteLLM metrics:

| Metric | Type | Use |
|--------|------|-----|
| `litellm_requests_metric_total` | counter | Rate, error rate per model |
| `litellm_request_duration_seconds` | histogram | p50/p95/p99 per model |
| `litellm_total_tokens` | counter | Token throughput |
| `litellm_input_tokens` | counter | Cost tracking (input) |
| `litellm_output_tokens` | counter | Cost tracking (output) |
| `litellm_remaining_requests_<model>` | gauge | Rate-limit headroom |

Key vLLM metrics:

| Metric | Type | Use |
|--------|------|-----|
| `vllm:num_requests_running` | gauge | Active request queue depth |
| `vllm:num_requests_waiting` | gauge | Queue backpressure |
| `vllm:gpu_cache_usage_perc` | gauge | KV cache utilization |
| `vllm:e2e_request_latency_seconds` | histogram | End-to-end latency |
| `vllm:generation_tokens_total` | counter | Throughput |

### Vector DB Metrics

| DB | Port | Metrics Path | Key Metrics |
|----|------|--------------|-------------|
| Qdrant | 6333 | `/metrics` | `qdrant_vectors_total`, `qdrant_rest_response_duration_seconds` |
| Weaviate | 2112 | `/metrics` | `weaviate_objects_total`, `weaviate_batch_durations_ms` |
| Milvus | 9091 | `/metrics` | `milvus_query_latency_ms`, `milvus_insert_total` |
| pgvector | via postgres_exporter | — | Query latency via generic PG metrics |

### Training Job Metrics (Pushgateway Pattern)

```python
# training_metrics.py — framework-agnostic; call push_epoch() each epoch
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from typing import Optional

def make_training_registry(model_name: str) -> tuple:
    """Create a per-run metrics registry. Call once per training run."""
    reg = CollectorRegistry()
    gauges = {
        "loss":     Gauge("training_loss",     "Loss by phase", ["phase"], registry=reg),
        "accuracy": Gauge("training_accuracy", "Accuracy by phase", ["phase"], registry=reg),
        "epoch":    Gauge("training_epoch",    "Current epoch", registry=reg),
        "lr":       Gauge("training_lr",       "Learning rate", registry=reg),
        "gpu_util": Gauge("training_gpu_util", "GPU utilization %", registry=reg),
        "step":     Gauge("training_step",     "Global step", registry=reg),
    }
    return reg, gauges


def push_epoch(
    registry: CollectorRegistry,
    gauges: dict,
    pushgateway_url: str,  # e.g. "pushgateway:9091"
    job_name: str,         # e.g. "finetune_llama3"
    run_id: str,
    epoch: int,
    logs: dict,
    gpu_util: Optional[float] = None,
) -> None:
    gauges["loss"].labels(phase="train").set(logs.get("loss", float("nan")))
    gauges["loss"].labels(phase="val").set(logs.get("val_loss", float("nan")))
    gauges["accuracy"].labels(phase="train").set(logs.get("accuracy", 0))
    gauges["accuracy"].labels(phase="val").set(logs.get("val_accuracy", 0))
    gauges["epoch"].set(epoch)
    gauges["lr"].set(logs.get("lr", logs.get("learning_rate", 0)))
    gauges["step"].set(logs.get("step", epoch))
    if gpu_util is not None:
        gauges["gpu_util"].set(gpu_util)
    push_to_gateway(
        pushgateway_url,
        job=job_name,
        registry=registry,
        grouping_key={"run_id": run_id},
    )
```

### Model Drift Monitoring

```python
# drift_metrics.py — push output distribution stats to detect drift over time
from prometheus_client import Histogram, push_to_gateway, CollectorRegistry

output_length_hist = Histogram(
    "model_output_length_tokens",
    "Distribution of output token counts",
    ["model"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000],
)

confidence_hist = Histogram(
    "model_output_confidence",
    "Distribution of model confidence scores",
    ["model"],
    buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99],
)

# Drift alert: if rolling p50 of output_length shifts > 20% vs baseline window
# PromQL: histogram_quantile(0.5, rate(model_output_length_tokens_bucket[1h]))
#         vs baseline stored as recording rule
```

### AI Architecture Dashboard Layout

Recommended folder/file structure — maps directly to Grafana folders via `foldersFromFilesStructure`:

```
dashboards/
├── overview/
│   └── ai-stack-health.json          # all services up/down, error rates, SLO status
├── inference/
│   ├── inference-overview.json       # per-model rate/latency/tokens (all servers)
│   ├── litellm-detail.json           # LiteLLM-specific: cost, rate limits, aliases
│   ├── vllm-detail.json              # vLLM-specific: KV cache, queue depth
│   └── model-slo.json                # SLO burn rate, error budget remaining
├── training/
│   ├── training-jobs.json            # active jobs, loss curves, epoch/step progress
│   └── gpu-utilization.json          # DCGM/ROCm metrics, temp, power, VRAM, NVLink
├── infrastructure/
│   ├── node-overview.json            # CPU/RAM/disk/network per host
│   └── vector-db-health.json         # collection size, latency, error rate
└── sre/
    ├── slo-overview.json             # all SLO burn rates + budget calendar
    └── alerts-active.json            # live alert inventory with runbook links
```

---

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Edit dashboards in Grafana UI | Lost on container rebuild; no review trail | Set `allowUiUpdates: false`; commit JSON to git |
| Label with `user_id`, `request_id` | Cardinality bomb; Prometheus OOM | Use Tempo traces for request-level data |
| Alert on GPU util > 80% | Training pegs GPU at 95%+ by design | Alert on `GPU_TEMP > 85°C` or job stall |
| 100% trace sampling for training | Storage cost explodes | Tail-sample: 100% errors, 1% success |
| `up == 0` as sole availability alert | Misses partial failures (errors without crash) | Combine with error rate + latency SLO |
| Push training metrics every step | Pushgateway flood; high cardinality | Push per epoch or per N steps only |
| Store Prometheus data > 90d locally | Disk fill; no off-host backup | `remote_write` to Mimir, Thanos, or Grafana Cloud |
| Skip `for:` on GPU alerts | Single-spike flapping at 3am | Minimum `for: 2m` on all GPU alerts |
| Hard-code Grafana org in API calls | Breaks multi-org; not portable | Use service accounts scoped per org |
| One dashboard with 50+ panels | Wall of graphs; 30s+ load time | Overview → service → instance drill-down hierarchy |
| Recording rule names without level prefix | Ambiguous; breaks PromQL conventions | Enforce `level:metric:operations` format |
| Omit `runbook_url:` annotation | On-call has no playbook at 3am | Every alert ships with a runbook link |
| Summary metric for cross-instance quantiles | Summaries cannot be aggregated | Use histogram; aggregate with `histogram_quantile()` |
| Hard-code hostnames or IPs in rules/configs | Breaks portability across environments | Use file_sd_configs + target JSON files |
| Static scrape targets for AI nodes | Requires Prometheus restart to add/remove | Use file_sd_configs; drop new JSON file = live |

## Quality Gates

Before shipping any monitoring change:

- [ ] All datasources provisioned via YAML or Terraform — no datasource added through UI
- [ ] All dashboards committed as JSON in git — provisioning YAML has `allowUiUpdates: false`
- [ ] Recording rules follow `level:metric:operations` naming convention
- [ ] Every alert has `runbook_url:` annotation
- [ ] `.env.example` updated with any new variables — no undocumented placeholders
- [ ] Cardinality check: `count by (job)({job=~".*"})` < 10,000 per scrape job
- [ ] GPU metrics flowing from DCGM/ROCm exporter before shipping GPU dashboard
- [ ] Pushgateway shows training job metrics within 60s of job start
- [ ] MWMBR burn-rate thresholds match stated SLO target (0.001 for 99.9%, etc.)
- [ ] Grafana API deploy is idempotent — running twice produces no errors or duplicates
- [ ] `docker compose up` from clean state loads all dashboards and datasources without manual steps
- [ ] No hostnames, IPs, or port numbers hard-coded in committed configs — all via file_sd or env vars

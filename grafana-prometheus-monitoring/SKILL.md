---
name: grafana-prometheus-monitoring
description: "Use this when: set up Grafana dashboards, configure Prometheus scraping, write recording rules, configure alerting, monitoring is broken, dashboards are wrong, cardinality is exploding, set up SLOs, configure Alertmanager, GPU monitoring, AI training metrics, model inference monitoring, LiteLLM metrics, Qdrant health, DCGM exporter, dashboards as code, provision Grafana without clicking, Grafana API, Grizzly, Grafonnet, Terraform grafana provider, kube-prometheus-stack, multi-burn-rate alerts, MWMBR, RED method, USE method, node exporter, cadvisor, blackbox exporter, Prometheus federation, remote write, high availability, Loki, Tempo, Mimir, AI workflow monitoring, training job metrics, inference monitoring, model serving SLO, drift detection, pushgateway"
---

# Grafana + Prometheus Monitoring

## Identity

You are a monitoring and observability engineer. Every configuration you produce is code-first:
no manual UI clicks, no one-off Grafana edits, no scrape targets added by hand. Dashboards live
in git. Rules live in files. Datasources are provisioned. The Grafana UI is read-only by
convention — `allowUiUpdates: false` is always set.

You produce working config blocks, deploy commands, and provisioning files. Not instructions to
click buttons.

## Stack Defaults

| Layer | Tool | Why |
|-------|------|-----|
| Metrics store | Prometheus (pull model) | Battle-tested, PromQL, recording rules, 15s scrape |
| Long-term storage | Grafana Mimir or Thanos | Object storage backend, horizontal scale, dedup |
| Visualization | Grafana (provisioned from git) | Variables, unified alerting, exemplar links |
| Logs | Loki + Promtail / Alloy | Label-indexed; 10x cheaper than ELK for structured logs |
| Traces | Tempo + OTEL Collector | Vendor-neutral; links to metrics and logs via exemplars |
| Alerting | Prometheus Alertmanager | group/route/silence; critical→PagerDuty, warning→Slack |
| GPU metrics | DCGM Exporter (NVIDIA) | CUDA-aware util, memory, power, NVLink, MIG |
| AI inference | vLLM /metrics, LiteLLM /metrics, Ollama /metrics | Native Prometheus endpoints |
| Training metrics | Prometheus Pushgateway | Push from batch job; scrape by Prometheus |
| Synthetic / probes | Blackbox Exporter | HTTP/TCP health, TLS cert expiry |
| Provisioning | Grafana provisioning YAMLs + Grafana API | Zero UI clicks; idempotent; git-tracked |
| Dashboards-as-code | Grafonnet (jsonnet) or Grizzly YAML | Programmatic; CI/CD deployable |
| IaC | Terraform grafana provider v3 | Folders, datasources, dashboards, alert policies |

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
- If NVIDIA GPU → `dcgm-exporter` on :9400; requires nvidia-container-runtime or nvidia runtime
- If AI inference service → scrape native `/metrics` endpoint (vLLM :8000, LiteLLM :29232, Ollama :11434)
- If training job (batch, exits after run) → push metrics to Pushgateway; scrape Pushgateway
- If external URL / certificate → Blackbox Exporter HTTP/TLS probe
- If Qdrant → scrape `:6333/metrics` (native Prometheus endpoint)
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

- Single Prometheus, < 90d retention → local storage sufficient; remote_write to Mimir/Thanos for analytics
- Multi-DC or > 6 months retention → Thanos with object store or Grafana Mimir
- HA: run 2 Prometheus replicas with identical configs + `--storage.tsdb.allow-overlapping-blocks`; deduplicate at Thanos Querier or Mimir query-frontend
- Alertmanager HA: 3 replicas minimum with gossip (`--cluster.peer`); route critical to PagerDuty

---

## Dashboard Provisioning (Code-First Patterns)

### Pattern 1 — Docker Compose + Provisioning YAMLs (default)

```yaml
# docker-compose.yml — monitoring stack
services:
  grafana:
    image: grafana/grafana:11.0.0
    volumes:
      - ./provisioning:/etc/grafana/provisioning:ro
      - ./dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: /var/lib/grafana/dashboards/home.json
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
      - --storage.tsdb.retention.time=90d
      - --storage.tsdb.allow-overlapping-blocks
      - --web.enable-lifecycle
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

volumes:
  grafana_data:
  prometheus_data:

networks:
  monitoring:
    enable_ipv6: false
```

```yaml
# provisioning/datasources/prometheus.yaml
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
# Import or overwrite a dashboard — safe to re-run
GRAFANA_URL=http://grafana:3000
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
    "url":"http://prometheus:9090","access":"proxy","isDefault":true
  }'

# Hot-reload Prometheus config (no restart needed)
curl -sf -X POST http://prometheus:9090/-/reload
```

### Pattern 3 — Grizzly CLI Deploy

```bash
# Install
go install github.com/grafana/grizzly/cmd/grr@latest

export GRAFANA_URL=http://grafana:3000
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
  url        = "http://prometheus:9090"
  is_default = true
  json_data_encoded = jsonencode({
    timeInterval = "15s"
    exemplarTraceIdDestinations = [
      { name = "traceID", datasourceUid = "tempo" }
    ]
  })
}

resource "grafana_rule_group" "inference_slo" {
  name             = "inference-slo"
  folder_uid       = grafana_folder.ai_monitoring.uid
  interval_seconds = 60
  # ... alert rules inline or imported from file
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
    cluster: dev-island
    env:     homelab

rule_files:
  - /etc/prometheus/rules/*.yaml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

remote_write:
  - url: http://mimir:9009/api/v1/push
    queue_config:
      max_samples_per_send: 10000
      batch_send_deadline: 5s

scrape_configs:
  # Hosts — add targets by dropping JSON files into /targets/nodes/; no restart
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

  # LiteLLM (dev-island stack — port 29232)
  - job_name: litellm
    static_configs:
      - targets: ["litellm:29232"]
        labels: { service: litellm, stack: dev_island }

  # Qdrant
  - job_name: qdrant
    static_configs:
      - targets: ["qdrant:6333"]
        labels: { service: qdrant }
    metric_relabel_configs:
      - source_labels: [collection]
        regex: ".{100,}"          # drop absurdly long collection names
        action: drop

  # GPU — xai node (RTX 5080) — set XAI_NODE_IP in your environment
  - job_name: dcgm_xai
    static_configs:
      - targets: ["<XAI_NODE_IP>:9400"]
        labels: { node: xai, gpu_model: rtx5080, role: gpu_worker }

  # GPU — DGX Spark — set DGX_NODE_IP in your environment
  - job_name: dcgm_dgx
    static_configs:
      - targets: ["<DGX_NODE_IP>:9400"]
        labels: { node: dgx_spark, role: training_node }

  # AI inference targets (file_sd — add new model servers without restart)
  - job_name: ai_inference
    file_sd_configs:
      - files: ["/etc/prometheus/targets/ai/*.json"]
        refresh_interval: 30s
    metric_relabel_configs:
      # Drop high-cardinality per-request labels if present
      - regex: "request_id|session_id|user_id|trace_id"
        action: labeldrop

  # Training pushgateway
  - job_name: pushgateway
    honor_labels: true             # preserve job/instance from pushed metrics
    static_configs:
      - targets: ["pushgateway:9091"]

  # Blackbox probes
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
```

```json
// /etc/prometheus/targets/nodes/xai.json
[{
  "targets": ["<XAI_NODE_IP>:9100"],
  "labels": { "job": "node", "instance": "xai", "role": "gpu_worker" }
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
      # Request rate per model (5m window)
      - record: model:http_requests:rate5m
        expr: sum by (model, status_code) (rate(litellm_requests_metric_total[5m]))

      # Error rate per model
      - record: model:http_errors:rate5m
        expr: |
          sum by (model) (rate(litellm_requests_metric_total{status_code=~"5.."}[5m]))
          / sum by (model) (rate(litellm_requests_metric_total[5m]))

      # p99 inference latency per model
      - record: model:inference_latency_seconds:p99_5m
        expr: |
          histogram_quantile(0.99,
            sum by (model, le) (rate(litellm_request_duration_seconds_bucket[5m])))

      # Token throughput per model
      - record: model:tokens_per_second:rate5m
        expr: sum by (model) (rate(litellm_total_tokens[5m]))

      # SLI: fraction of good requests (2xx, latency < 1s)
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
        expr: avg by (node, gpu) (DCGM_FI_DEV_GPU_UTIL)

      - record: node:gpu_memory_used_ratio:avg5m
        expr: |
          avg by (node, gpu) (DCGM_FI_DEV_FB_USED)
          / (avg by (node, gpu) (DCGM_FI_DEV_FB_USED) + avg by (node, gpu) (DCGM_FI_DEV_FB_FREE))

      - record: node:gpu_power_watts:avg5m
        expr: avg by (node, gpu) (DCGM_FI_DEV_POWER_USAGE)

  - name: training_recording
    interval: 60s
    rules:
      # Track last push time per training run
      - record: training_job:last_push_age_seconds:gauge
        expr: time() - push_time_seconds{job="pushgateway"}
```

---

## Alerting Rules

```yaml
# /etc/prometheus/rules/ai_alerts.yaml
groups:
  - name: ai_inference_alerts
    rules:
      - alert: InferenceHighErrorRate
        expr: model:http_errors:rate5m > 0.05
        for: 5m
        labels:
          severity: warning
          team: ai
        annotations:
          summary: "{{ $labels.model }} error rate {{ $value | humanizePercentage }}"
          runbook_url: "https://wiki.internal/runbooks/inference-errors"

      - alert: InferenceHighLatencyP99
        expr: model:inference_latency_seconds:p99_5m > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.model }} p99 {{ $value | humanizeDuration }}"
          runbook_url: "https://wiki.internal/runbooks/inference-latency"

      - alert: LiteLLMDown
        expr: up{job="litellm"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "LiteLLM proxy on dev-island is down"
          runbook_url: "https://wiki.internal/runbooks/litellm-down"

  - name: gpu_alerts
    rules:
      - alert: GPUHighTemperature
        expr: DCGM_FI_DEV_GPU_TEMP > 85
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} at {{ $value }}°C"
          runbook_url: "https://wiki.internal/runbooks/gpu-thermal"

      - alert: GPUMemoryNearFull
        expr: node:gpu_memory_used_ratio:avg5m > 0.92
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} memory {{ $value | humanizePercentage }}"
          runbook_url: "https://wiki.internal/runbooks/gpu-memory"

      - alert: GPUUnderutilizedDuringTraining
        expr: |
          node:gpu_utilization:avg5m < 10
          and on (node) training_job:last_push_age_seconds:gauge < 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} underutilized during active training"

  - name: training_alerts
    rules:
      - alert: TrainingJobStalled
        expr: training_job:last_push_age_seconds:gauge > 3600
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Training job {{ $labels.exported_job }} has not pushed metrics in 1h"
          runbook_url: "https://wiki.internal/runbooks/training-stalled"

      - alert: TrainingLossNaN
        expr: training_loss{phase="train"} != training_loss{phase="train"}
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Training loss is NaN for job {{ $labels.exported_job }}"

  - name: slo_mwmbr
    # Multi-window multi-burn-rate SLO alerts (SLO: 99.9% availability = 0.1% error budget)
    rules:
      - alert: SLOBurnRateFast          # 14.4× burn → exhausts budget in 1h
        expr: |
          (job:slo_error_rate:rate1h > (14.4 * 0.001))
          and
          (job:slo_error_rate:rate5m > (14.4 * 0.001))
        for: 2m
        labels:
          severity: critical
          window: fast
        annotations:
          summary: "{{ $labels.job }} burning SLO budget at {{ $value | humanizePercentage }} (fast window)"
          runbook_url: "https://wiki.internal/runbooks/slo-burn"

      - alert: SLOBurnRateSlow           # 6× burn → exhausts budget in 6h
        expr: |
          (job:slo_error_rate:rate6h > (6 * 0.001))
          and
          (job:slo_error_rate:rate30m > (6 * 0.001))
        for: 15m
        labels:
          severity: warning
          window: slow
        annotations:
          summary: "{{ $labels.job }} burning SLO budget at {{ $value | humanizePercentage }} (slow window)"
          runbook_url: "https://wiki.internal/runbooks/slo-burn"
```

---

## AI / ML Monitoring

### GPU (DCGM Exporter) — Compose Service

```yaml
# Add to monitoring docker-compose.yml or xai node compose
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

Key DCGM metrics to dashboard:

| Metric | Meaning | Alert Threshold |
|--------|---------|-----------------|
| `DCGM_FI_DEV_GPU_UTIL` | Compute utilization % | < 10% during training |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth % | — |
| `DCGM_FI_DEV_FB_USED` | VRAM used (MiB) | > 92% of FB_FREE+FB_USED |
| `DCGM_FI_DEV_FB_FREE` | VRAM free (MiB) | — |
| `DCGM_FI_DEV_GPU_TEMP` | Temperature °C | > 85°C |
| `DCGM_FI_DEV_POWER_USAGE` | Power draw (W) | > TDP × 0.95 |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | NVLink bytes/s | — |
| `DCGM_FI_PROF_TENSOR_ACTIVE` | Tensor core utilization | — |

### Training Job Metrics (Pushgateway Pattern)

```python
# training_metrics.py — call on_epoch_end() each epoch
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def make_registry(model_name: str, run_id: str):
    reg = CollectorRegistry()
    return reg, {
        "loss":     Gauge("training_loss",     "Training loss",     ["phase"], registry=reg),
        "accuracy": Gauge("training_accuracy", "Training accuracy", ["phase"], registry=reg),
        "epoch":    Gauge("training_epoch",    "Current epoch",               registry=reg),
        "lr":       Gauge("training_lr",       "Learning rate",               registry=reg),
        "gpu_util": Gauge("training_gpu_util", "GPU utilization during step",  registry=reg),
    }, model_name, run_id, reg


def push_epoch(metrics: dict, reg, model_name: str, run_id: str, epoch: int, logs: dict):
    metrics["loss"].labels(phase="train").set(logs.get("loss", float("nan")))
    metrics["loss"].labels(phase="val").set(logs.get("val_loss", float("nan")))
    metrics["accuracy"].labels(phase="train").set(logs.get("accuracy", 0))
    metrics["accuracy"].labels(phase="val").set(logs.get("val_accuracy", 0))
    metrics["epoch"].set(epoch)
    metrics["lr"].set(logs.get("lr", 0))
    push_to_gateway(
        "pushgateway:9091",
        job=f"training_{model_name}",
        registry=reg,
        grouping_key={"run_id": run_id},
    )
```

### LiteLLM Metrics (dev-island stack, port 29232)

Enable in `config.yaml`:
```yaml
general_settings:
  enable_prometheus: true
```

Key LiteLLM metrics:

| Metric | Type | Dashboard Use |
|--------|------|---------------|
| `litellm_requests_metric_total` | counter | Request rate, error rate per model |
| `litellm_request_duration_seconds` | histogram | p50/p95/p99 per model |
| `litellm_total_tokens` | counter | Token throughput per model |
| `litellm_input_tokens` | counter | Cost input tracking |
| `litellm_output_tokens` | counter | Cost output tracking |
| `litellm_remaining_requests_<model>` | gauge | Rate-limit headroom |

### Qdrant Metrics (port 6333)

Key metrics to dashboard:

| Metric | Alert |
|--------|-------|
| `qdrant_collections_total` | — |
| `qdrant_vectors_total` | growth rate > expected |
| `qdrant_rest_response_duration_seconds` | p99 > 100ms |
| `qdrant_rest_responses_total{status!~"2.."}` | error rate > 0% |
| `qdrant_grpc_responses_total` | error_rate > 0% |

Collections to monitor: `codebase.embeddings`, `docs.offline`, `panopticon.feeds`, `training.datasets`

### Model Drift Monitoring (Custom Metrics)

```python
# Push distribution stats on inference output to detect drift
from prometheus_client import Histogram, Counter, push_to_gateway, CollectorRegistry

output_length_hist = Histogram(
    "model_output_length_tokens",
    "Output token count distribution",
    ["model"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000]
)

confidence_hist = Histogram(
    "model_output_confidence",
    "Model output confidence score",
    ["model"],
    buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99]
)

# Alert if rolling output_length p50 shifts > 20% vs baseline window
# use: histogram_quantile(0.5, rate(model_output_length_tokens_bucket[1h]))
```

### AI Architecture Dashboard Layout

Recommended folder structure:

```
dashboards/
├── overview/
│   └── ai-stack-health.json          # all services up/down, error rates
├── inference/
│   ├── litellm-overview.json         # per-model rate/latency/tokens
│   └── model-slo.json                # SLO burn rate, error budget
├── training/
│   ├── training-jobs.json            # loss curves, epoch progress, GPU util
│   └── gpu-utilization.json          # DCGM metrics, temp, power, memory
├── infrastructure/
│   ├── node-overview.json            # CPU/RAM/disk per host
│   └── qdrant-health.json            # collection metrics, latency
└── sre/
    ├── slo-overview.json             # all SLO burn rates
    └── alerts-active.json            # active alert inventory
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
    - match:
        severity: critical
      receiver: pagerduty-critical
      continue: false
    - match:
        severity: warning
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
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: [alertname, cluster, service]
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
| Push training metrics every step | Pushgateway floods; high cardinality | Push per epoch or per N steps only |
| Store Prometheus data > 90d locally | Disk fill; no disaster recovery | `remote_write` to Mimir or Thanos |
| Skip `for:` on GPU alerts | Single-spike flapping at 3am | Minimum `for: 2m` on all GPU alerts |
| Hard-code Grafana org in API calls | Breaks multi-org; hard to migrate | Use service accounts scoped per org |
| One dashboard with 50+ panels | Wall of graphs; 30s load time | Overview → service → instance drill-down |
| record rule names without level prefix | Ambiguous; breaks PromQL conventions | Use `level:metric:operations` format |
| Omit `runbook_url:` annotation | On-call has no playbook at 3am | Every alert ships with a runbook link |
| Summary metric for cross-instance quantiles | Summaries cannot be aggregated | Use histogram; aggregate with `histogram_quantile()` |

## Quality Gates

Before shipping any monitoring change:

- [ ] All datasources provisioned via YAML or Terraform — no datasource added through UI
- [ ] All dashboards committed as JSON in git — provisioning YAML has `allowUiUpdates: false`
- [ ] Recording rules follow `level:metric:operations` naming convention
- [ ] Every alert has `runbook_url:` annotation
- [ ] Cardinality check passes: `count by (job)({job=~".*"})` < 10,000 per scrape job
- [ ] GPU metrics flowing from DCGM exporter before shipping GPU dashboard
- [ ] Pushgateway shows training job metrics within 60s of job start
- [ ] MWMBR alerts tested: fast window fires within 2m of simulated error spike
- [ ] Grafana API deploy is idempotent — running twice produces no errors and no duplicate dashboards
- [ ] `docker compose up` from clean state loads all dashboards and datasources without manual steps

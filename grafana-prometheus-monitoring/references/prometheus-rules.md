# Prometheus Recording Rules, Alerts & Alertmanager

Naming convention: `level:metric:operations`. Every alert MUST carry `runbook_url`.

---

## Recording Rules

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

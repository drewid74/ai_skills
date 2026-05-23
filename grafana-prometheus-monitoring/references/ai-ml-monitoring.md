# AI / ML Monitoring

GPU exporters, inference servers, vector DBs, training jobs, drift detection, dashboard layout.

---

## GPU Exporters

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

---

## AI Inference Servers — Native Metrics Endpoints

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

---

## Vector DB Metrics

| DB | Port | Metrics Path | Key Metrics |
|----|------|--------------|-------------|
| Qdrant | 6333 | `/metrics` | `qdrant_vectors_total`, `qdrant_rest_response_duration_seconds` |
| Weaviate | 2112 | `/metrics` | `weaviate_objects_total`, `weaviate_batch_durations_ms` |
| Milvus | 9091 | `/metrics` | `milvus_query_latency_ms`, `milvus_insert_total` |
| pgvector | via postgres_exporter | — | Query latency via generic PG metrics |

---

## Training Job Metrics (Pushgateway Pattern)

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

---

## Model Drift Monitoring

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

---

## AI Architecture Dashboard Layout

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

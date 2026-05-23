# Prometheus Scrape Configuration

File-SD pattern — add targets without restarting Prometheus.

---

## prometheus.yml — Full Config

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

---

## File-SD Target Templates

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

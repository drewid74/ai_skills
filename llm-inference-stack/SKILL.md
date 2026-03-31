---
name: llm-inference-stack
description: "Use this skill whenever the user wants to set up, manage, optimize, or troubleshoot self-hosted LLM inference. Triggers include: any mention of 'Ollama', 'vLLM', 'NVIDIA NIM', 'NIM container', 'TensorRT-LLM', 'SGLang', 'llama.cpp', 'LiteLLM', 'OpenRouter', 'inference server', 'model serving', 'LLM hosting', 'GPU inference', 'model routing', 'load balancing LLM', 'GGUF', 'quantization', 'context window', 'tokens per second', 'VRAM', 'model selection', 'embedding server', 'vector embeddings', 'local AI', 'self-hosted AI', 'Open WebUI', 'text-generation-inference', 'TGI', or requests to deploy, benchmark, or compare language models on local hardware. Also use when the user asks about GPU memory requirements, model quantization tradeoffs, multi-GPU setups, inference optimization, or building a unified API gateway across multiple inference backends. If someone says 'run a model locally' or 'which model fits my GPU', use this skill."
---

# LLM Inference Stack

## Overview
Deploy, route, and optimize self-hosted LLM inference from single-GPU development boxes to multi-node production clusters. Each backend trades simplicity, throughput, and hardware support differently. Pick based on your constraints (model size, VRAM, latency requirements, concurrency demand).

## Inference Backends Compared

### Ollama
**Best for:** Experimentation, lightweight deployments, easy multi-model switching.
- Supports GGUF models with automatic quantization selection
- Single-model active at a time (models swap in/out of VRAM)
- OpenAI-compatible API at `http://<INFERENCE_HOST>:11434/v1/chat/completions`
- Docker: `docker run -d --gpus all -p 11434:11434 ollama/ollama`
- No batching (each request waits for GPU to free up)

### vLLM
**Best for:** Production throughput, multi-GPU scaling, structured generation.
- Continuous batching + PagedAttention = high concurrency, minimal memory fragmentation
- Supports HuggingFace models, AWQ/GPTQ quantization
- Tensor parallelism for multi-GPU, pipeline parallelism for very large models
- OpenAI-compatible API at `http://<INFERENCE_HOST>:8000/v1/chat/completions`
- Higher startup time, more memory overhead

### NVIDIA NIM
**Best for:** Maximum NVIDIA hardware performance, production deployments with NGC support.
- TensorRT-LLM backend, auto-detects quantization and model architecture
- Requires NGC API key (free tier available)
- Docker: `docker run --gpus all --api-key <NGC_KEY> nvcr.io/nvidia/nim:llm-<MODEL_NAME>`
- Best throughput/latency on H100, A100, RTX series

### llama.cpp / llama-server
**Best for:** CPU inference, edge deployment, minimal dependencies.
- GGUF format, wide quantization options (Q2–Q8)
- Runs on CPU + Metal/CUDA/SYCL
- Server mode: `./llama-server -m <MODEL>.gguf -ngl 33 --port 8000`
- Low overhead, simple stateless scaling

### SGLang
**Best for:** Structured generation, complex prompts with guaranteed format.
- RadixAttention for prompt caching, schema-guided generation
- Good for complex agentic workflows
- Docker with vLLM backend

### Text Generation Inference (TGI)
**Best for:** HuggingFace ecosystem alignment, many model architectures.
- HuggingFace's official production server
- Flash Attention, continuous batching
- Docker: `docker run --gpus all -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest`

## VRAM Requirements & Model Selection

Calculate VRAM needed: **parameters × bytes_per_param + overhead**.

| Quantization | Bytes/Param | 7B Model | 13B | 34B | 70B |
|--------------|------------|----------|-----|-----|-----|
| FP16         | 2.0        | 14GB     | 26GB| 68GB| 140GB |
| Q8           | 1.0        | 7GB      | 13GB| 34GB| 70GB |
| Q6_K (GGUF)  | 0.75       | 5.2GB    | 9.7GB | 25.5GB | 52.5GB |
| Q5_K_M (GGUF)| 0.61       | 4.3GB    | 7.9GB | 20.7GB | 42.7GB |
| Q4_K_M (GGUF)| 0.48       | 3.4GB    | 6.2GB | 16.3GB | 33.6GB |

Add **1–2GB overhead** for KV cache, runtime buffers, and safety margin. Context length increases KV cache: 8K tokens = ~2x more memory than 2K.

**GPU VRAM tiers & recommendations:**
- 8GB: Q4_K_M up to 7B, Q5_K_M up to 3B
- 12GB: Q5_K_M up to 7B, Q4_K_M up to 13B
- 16GB: Q4_K_M up to 13B, Q5_K_M up to 13B, FP16 up to 7B
- 24GB: FP16 up to 13B, Q4_K_M up to 34B
- 48GB: FP16 up to 34B, Q4_K_M up to 70B
- 80GB: FP16 up to 70B

Monitor with `nvidia-smi` during inference. Peak VRAM = base + per-batch KV cache.

## Quantization Essentials

**Why quantize:** Fit larger models, faster inference, negligible quality loss at Q4+.

**Quality hierarchy:** FP16 > Q8 > Q6_K > Q5_K_M > Q4_K_M > Q4_0 > Q2

**Format-to-backend mapping:**
- GGUF → Ollama, llama.cpp, LiteLLM
- AWQ → vLLM, TGI
- GPTQ → vLLM, TGI
- FP8/INT8 → TensorRT-LLM (NIM)

**When to use which:**
- Q4_K_M: sweet spot (3.4–4.8GB per 7B), minimal quality loss
- Q5_K_M: if you have VRAM, noticeable quality improvement
- Q8: if VRAM allows, best for long context / reasoning tasks
- Q2–Q3: only for memory-constrained edge, acceptable for classification tasks

Find quantized models on HuggingFace (filter by GGUF or AWQ tags) or use AutoGPTQ/llama.cpp to quantize yourself.

## Embedding Servers

Deploy embeddings separately to avoid blocking inference:
- Common models: `nomic-embed-text` (768-dim, fast), `all-MiniLM-L6-v2` (384-dim, lightweight), `BGE-small-en` (384-dim, retrieval), `E5-large` (1024-dim, high quality)
- Dimension tradeoffs: smaller = faster + less VRAM, larger = better semantic quality
- Deploy via Ollama: `ollama pull nomic-embed-text`
- Dedicated server: `docker run -p 8001:8001 <EMBEDDING_IMAGE>`
- Use cases: RAG pipelines (query embedding), document clustering, semantic search, re-ranking

## Unified API Gateway (LiteLLM)

Route multiple inference backends through a single OpenAI-compatible endpoint.

**Why:** Avoid vendor lock-in, load balance, fallback chains, unified rate limiting.

**Docker Compose example:**
```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main
    ports:
      - "8000:8000"
    environment:
      - LITELLM_LOG=DEBUG
    volumes:
      - ./config.yaml:/app/config.yaml
    command: litellm --config /app/config.yaml

  ollama:
    image: ollama/ollama
    gpus: all
    ports:
      - "11434:11434"

  vllm:
    image: vllm/vllm-openai:latest
    gpus: all
    ports:
      - "8001:8000"
    environment:
      - MODEL_NAME=<MODEL_NAME>
```

**config.yaml for LiteLLM:**
```yaml
model_list:
  - model_name: "default"
    litellm_params:
      model: "ollama/<MODEL_NAME>"
      api_base: "http://ollama:11434/v1"
  - model_name: "fast"
    litellm_params:
      model: "openai/<MODEL_NAME>"
      api_base: "http://vllm:8000/v1"

router_settings:
  timeout: 60
  enable_fallback: true
  fallback_route_order: ["fast", "default"]
  health_check_enabled: true
```

Clients call: `curl http://<INFERENCE_HOST>:8000/v1/chat/completions -H "Authorization: Bearer <API_KEY>"`

## Multi-Node Topology

Scale horizontally by separating concerns:
- **Large models:** RTX 4090 / A100 (inference only, no embedding overhead)
- **Embeddings:** RTX 4070 / A5000 (shared among apps)
- **Small utility models:** CPU-only inference node
- **Gateway:** CPU-only Docker host running LiteLLM

**Network:** Dedicate a low-latency VLAN for inter-node traffic (high bandwidth, ~100µs latency). All clients reach the gateway; gateway routes to inference nodes internally.

**Docker setup:** Overlay networks for multi-node isolation, or host networking if latency-critical.

## Monitoring & Benchmarking

**Key metrics:**
- Throughput: tokens/second (higher = better)
- TTFT (time-to-first-token): latency until first output
- VRAM usage: sustained and peak
- Queue depth: waiting requests

**Benchmarking:**
```bash
# Simple curl benchmark with timing
time curl http://<INFERENCE_HOST>:8000/v1/chat/completions \
  -d '{"model":"<MODEL>","messages":[{"role":"user","content":"Count to 10"}]}'
```

**Monitoring setup:**
- vLLM and LiteLLM expose `/metrics` in Prometheus format
- Scrape every 15s, retention 7+ days
- Grafana dashboards: graph tokens/sec, VRAM, request latency
- Alerts: VRAM > 90%, generation speed drop > 30%, backend down

## Docker Compose Health Checks

Ensure inference containers restart on failure:
```yaml
services:
  inference:
    image: ollama/ollama
    gpus: all
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

GPU passthrough (NVIDIA):
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Model won't load | Insufficient VRAM or format mismatch | Check `nvidia-smi`, verify GGUF/quantization format matches backend |
| Slow generation (tokens/sec drop) | High batch size, long context, undersized quantization | Reduce max_tokens, lower context window, try Q5_K_M instead of Q4_K_M |
| Connection refused | Model still loading or port not mapped | Wait (large models take minutes), check Docker logs, verify port binding |
| IPv6 issues in Docker | aiohttp tries IPv6 first | Add `enable_ipv6: false` to compose network config, use AF_INET in connector |
| LiteLLM routing fails | Backend down or model_name mismatch | Test each backend independently with curl, verify alias names in config.yaml |
| Out of memory mid-conversation | Cumulative KV cache grows | Use shorter context windows, set `max_new_tokens=256`, scale to larger VRAM tier |

Always verify single-backend health before adding a gateway. Start inference with logs: `docker logs -f <CONTAINER>`.

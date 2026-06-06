---
name: llm-inference-stack
description: "Use this when: run a model locally, which model fits my GPU, my inference is too slow, serve LLM in production, how to quantize a model, too many concurrent users, self-host an AI, set up Ollama, vLLM vs Ollama, route between multiple models, VRAM out of memory, model won't load, tokens per second too low, pick a quantization format, LiteLLM gateway setup, what model fits 8GB VRAM, OpenAI-compatible local endpoint"
---

# LLM Inference Stack

## Identity
You are an LLM inference engineer. Pick a backend and commit — no "it depends" non-answers. Never suggest a model without confirming it fits the user's VRAM budget.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Dev / single-user | Ollama | Zero-config, GGUF auto-download, OpenAI-compatible |
| Production throughput | vLLM | PagedAttention + continuous batching; handles concurrent users |
| Structured output | SGLang | RadixAttention prompt caching + schema-guided generation |
| CPU / edge | llama.cpp / llama-server | GGUF, runs on CPU+Metal/CUDA, minimal dependencies |
| NVIDIA production | NIM (TensorRT-LLM) | Best throughput/latency on H100/A100/RTX; NGC API key required |
| API gateway / multi-backend | LiteLLM | Single OpenAI-compatible endpoint; fallback chains |
| Quantization format (GGUF) | Q4_K_M | 3.4GB/7B, <3% quality loss; Q5_K_M if VRAM allows |
| Quantization format (GPU) | AWQ | Better quality than GPTQ; vLLM + TGI compatible |

## Decision Framework

### Which backend?
- If dev / quick test → Ollama (`docker run -d --gpus all ollama/ollama`)
- If >10 concurrent users OR need batching → vLLM
- If CPU-only or edge → llama-server (llama.cpp)
- If need JSON/regex-constrained output → SGLang
- If H100/A100 production → NIM (`nvcr.io/nvidia/nim:llm-<MODEL>`)
- Default → Ollama for dev; vLLM behind LiteLLM for production

### Which quantization?
- If Ollama / llama.cpp → GGUF; start Q4_K_M, upgrade to Q5_K_M if VRAM allows
- If vLLM / TGI → AWQ (quality) or GPTQ (compatibility)
- If H100/A100 → FP8 via TensorRT-LLM / NIM
- If VRAM very tight → Q4_0 (last resort, noticeable degradation)
- Default → Q4_K_M GGUF for dev; AWQ for production GPU

### Which model fits my GPU?
- 8GB → Q4_K_M up to 7B
- 12GB → Q5_K_M up to 7B, Q4_K_M up to 13B
- 16GB → FP16 up to 7B, Q4_K_M up to 13B
- 24GB → FP16 up to 13B, Q4_K_M up to 34B
- 48GB → FP16 up to 34B, Q4_K_M up to 70B
- 80GB → FP16 up to 70B

### Multi-backend routing (LiteLLM)
- If single backend → skip LiteLLM; call backend directly
- If 2+ backends OR need fallback → LiteLLM with `config.yaml` model_list
- If embeddings needed → separate container (nomic-embed-text via Ollama)
- Default → LiteLLM gateway on CPU node; inference on GPU nodes

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Mix GGUF into vLLM | vLLM doesn't support GGUF; silent load failure | Use HF model ID or AWQ/GPTQ for vLLM |
| Skip health checks in compose | Container restarts silently; requests drop | Add `healthcheck` + `restart: unless-stopped` |
| Run embeddings on inference GPU | Competes for VRAM; degrades generation latency | Separate embedding container on dedicated GPU or CPU |
| Size model without KV cache overhead | OOM mid-conversation as context grows | Budget +2GB for KV cache; set `max_new_tokens` limits |
| Assume IPv4 in Docker networking | aiohttp tries IPv6 first; connection refused | `enable_ipv6: false` in compose networks config |

## Quality Gates
- [ ] `nvidia-smi` confirms model loaded and VRAM within budget
- [ ] Single-backend curl test passes before adding LiteLLM gateway
- [ ] Tokens/sec and TTFT measured at target concurrency
- [ ] Health check endpoints responding on all containers
- [ ] Embedding model on separate endpoint (not sharing inference GPU)
- [ ] Fallback chain tested: primary down → secondary responds correctly

## Reference
```
VRAM formula: params × bytes_per_param + KV_cache_overhead
  FP16=2B/param | Q8=1B/param | Q5_K_M=0.61B | Q4_K_M=0.48B
  KV cache: 8K context ≈ 2× 2K context; cap with max_new_tokens

Ollama API:  http://host:11434/v1/chat/completions
vLLM API:   http://host:8000/v1/chat/completions
TGI API:    http://host:8080/v1/chat/completions
Metrics:    vLLM /metrics, LiteLLM /metrics (Prometheus)
```

---

## VRAM Table

| Quant | Bytes/param | 7B | 13B | 34B | 70B |
|-------|------------|-----|-----|-----|-----|
| FP16 | 2.0 | 14GB | 26GB | 68GB | 140GB |
| Q8 | 1.0 | 7GB | 13GB | 34GB | 70GB |
| Q5_K_M | 0.61 | 4.3GB | 7.9GB | 20.7GB | 42.7GB |
| Q4_K_M | 0.48 | 3.4GB | 6.2GB | 16.3GB | 33.6GB |

Add 1–2GB for KV cache + runtime buffers. Context length increases KV cache: 8K ≈ 2× 2K.

## Quantization Format Map

| Format | Backends | Quality |
|--------|----------|---------|
| GGUF Q4_K_M | Ollama, llama.cpp | Good (sweet spot) |
| GGUF Q5_K_M | Ollama, llama.cpp | Better |
| AWQ | vLLM, TGI | Best GPU |
| GPTQ | vLLM, TGI | Good GPU |
| FP8/INT8 | TensorRT-LLM/NIM | Production H100/A100 |

## LiteLLM Gateway

```yaml
# docker-compose.yml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main
    ports: ["8000:8000"]
    volumes: ["./config.yaml:/app/config.yaml"]
    command: litellm --config /app/config.yaml
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices: [{driver: nvidia, count: all, capabilities: [gpu]}]
    ports: ["11434:11434"]
```

```yaml
# config.yaml
model_list:
  - model_name: "default"
    litellm_params:
      model: "ollama/<MODEL>"
      api_base: "http://ollama:11434/v1"
  - model_name: "fast"
    litellm_params:
      model: "openai/<MODEL>"
      api_base: "http://vllm:8000/v1"
router_settings:
  timeout: 60
  enable_fallback: true
  fallback_route_order: ["fast", "default"]
  health_check_enabled: true
```

## Embeddings

Deploy separately to avoid blocking inference:

| Model | Dims | Use |
|-------|------|-----|
| nomic-embed-text | 768 | Fast, good general retrieval |
| all-MiniLM-L6-v2 | 384 | Lightweight |
| BGE-small-en | 384 | Retrieval optimized |
| E5-large | 1024 | High quality |

```bash
ollama pull nomic-embed-text  # simplest path
```

## Monitoring

```bash
# Quick benchmark
time curl http://host:8000/v1/chat/completions \
  -d '{"model":"<MODEL>","messages":[{"role":"user","content":"Count to 10"}]}'
```

vLLM and LiteLLM expose `/metrics` in Prometheus format. Alert on: VRAM >90%, tok/s drop >30%, backend down.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Model won't load | Insufficient VRAM or format mismatch | Check `nvidia-smi`; verify GGUF/AWQ matches backend |
| Slow generation | High batch, long context, wrong quant | Lower max_tokens, try Q5 not Q4, check concurrency |
| Connection refused | Model still loading | Wait (large models take minutes); check `docker logs` |
| IPv6 error | aiohttp tries IPv6 first | `enable_ipv6: false` in compose network |
| LiteLLM routing fails | Backend down or model_name mismatch | Test each backend with curl first |
| OOM mid-conversation | KV cache grows with context | Set `max_new_tokens=256`; use shorter context window |

Always verify single-backend health before adding the gateway. Start with logs: `docker logs -f <CONTAINER>`.

> For Docker Compose patterns, health checks, and GPU passthrough syntax, see `docker-selfhost`.

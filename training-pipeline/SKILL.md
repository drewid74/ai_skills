---
name: training-pipeline
description: "Use this when: fine-tune my model, my training loss won't converge, out of memory during training, LoRA vs full fine-tune, my GPU is too small, set up distributed training, model is overfitting, pick a learning rate, prepare a training dataset, QLoRA on consumer GPU, instruction tuning, run training on multiple GPUs, my val loss is diverging, pick batch size, configure DeepSpeed, what rank for LoRA, how many training epochs"
---

# Training Pipeline

## Identity
You are an LLM training engineer. Default to LoRA unless given a reason not to. Never recommend a hyperparameter without stating what to watch to know if it's working.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Fine-tuning method | LoRA (r=16, alpha=32) | 80% VRAM savings vs full, swappable adapters |
| Low-VRAM option | QLoRA (4-bit base + LoRA) | 7B fits 8GB GPU, 13B fits 16GB |
| Training framework | HuggingFace Trainer + PEFT | Handles LR schedule, checkpointing, DDP automatically |
| Multi-precision | bf16 (Ampere+) | No loss scaling needed; fp16 on older GPUs |
| Multi-GPU | DDP via `torchrun` → FSDP if OOM | DDP is simpler; FSDP shards params across GPUs |
| Distributed scale | DeepSpeed ZeRO Stage 2 | 8× memory savings; Stage 3 only if model won't fit |
| Experiment tracking | MLflow (self-hosted) or W&B | Compare runs, track checkpoints, log artifacts |
| Dataset format | Alpaca JSON or chat messages list | Alpaca for tasks; chat format for dialogue models |

## Decision Framework

### Which fine-tuning method?
- If VRAM ≥ model_size × 4 AND need max quality → Full fine-tune
- If 8–24GB GPU → QLoRA (4-bit base + LoRA adapters)
- If 24–80GB GPU → LoRA (fp16 base, r=16)
- If domain shift (new vocabulary) → Continued pretraining first, then instruction tune
- Default → LoRA r=16, alpha=32, target `q_proj`+`v_proj`

### Learning rate & schedule
- If LoRA → start 2e-4, cosine decay, 3% warmup steps
- If full fine-tune → start 5e-5, cosine decay
- If loss is NaN → halve LR, switch fp16→bf16, check data for inf/NaN
- If val loss not moving after 100 steps → 10× LR sweep on 1% data first
- Default → cosine decay scheduler, warmup=0.03×total_steps

### Batch size & gradient accumulation
- If OOM → halve batch size, double gradient_accumulation_steps
- Target effective batch = per_device × accum_steps × n_gpus ≥ 32
- Default → per_device_batch=4, accumulation=8 (effective=32 on 1 GPU)

### Distributed training
- If 1 GPU → HuggingFace Trainer + `torch.compile()`
- If 2–8 GPUs, model fits 1 GPU → DDP (`torchrun --nproc_per_node=N`)
- If model won't fit 1 GPU → FSDP or DeepSpeed ZeRO-3 with CPU offload
- Default → DDP; add DeepSpeed Stage 2 config for memory pressure

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Start with full fine-tune | 4–6× VRAM of model size; rarely justified | LoRA first; full fine-tune only if LoRA quality insufficient |
| Skip data deduplication | Duplicates inflate metrics, cause memorization | MinHash dedup before training; exact-hash for identical rows |
| Train for 10+ epochs on small data | Guaranteed overfitting; val loss diverges | 1–3 epochs; watch val loss every 50–100 steps |
| Use fp16 on Ampere+ GPUs | Needs loss scaling; unstable on some models | bf16: no scaling needed, more numerically stable |
| Eval only at end of training | Miss early divergence or optimal checkpoint | Eval every N steps; use `load_best_model_at_end=True` |

## Quality Gates
- [ ] Val loss decreases steadily (not diverging or flat after warmup)
- [ ] `nvidia-smi` shows >85% GPU utilization during training
- [ ] Deduplication run; spot-checked 50+ samples for quality issues
- [ ] Effective batch size ≥ 32 (via accumulation if needed)
- [ ] Compared to baseline (same eval data, no fine-tuning)
- [ ] Best checkpoint saved by val loss, not just final epoch

## Reference
```
LoRA VRAM: model_fp16 × 1.1 + activations + optimizer ≈ 16.9GB for 7B (r=16)
Full FT VRAM: model + gradients + activations ≈ 29.5GB for 7B
QLoRA: 7B→~8GB, 13B→~14GB, 34B→~22GB (4-bit base)
LR ranges: LoRA 1e-4–3e-4 | Full FT 5e-5–1e-4 | Continued pretraining 1e-5–5e-5
```

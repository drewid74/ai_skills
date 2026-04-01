---
title: ML Engineer Super Agent
description: Complete ML pipeline orchestration—training, inference, optimization. Fine-tuning strategies (LoRA/QLoRA/full), distributed training (DeepSpeed/FSDP), quantization advisor, VRAM calculators, dataset curation, experiment comparison, cost estimation, and production deployment patterns.
trigger: |
  I need to [train|fine-tune|optimize|deploy|compare] [a model|inference stack|training runs|datasets|quantization strategies]
  How do I [estimate costs|calculate VRAM|pick quantization|optimize batch size|curate data|scale inference]?
  [LoRA|QLoRA|full fine-tuning|vLLM|Ollama|quantization|distributed training] best practices?
  A/B test [models|quantization|hyperparameters] with statistical significance?
---

# ML Engineer: Complete Pipeline Orchestration

You are a universal ML systems expert covering training pipelines, inference stacks, optimization, and production deployment. Explain the WHY behind every pattern—not just the HOW.

## TRAINING PIPELINE ARCHITECTURE

### Why LoRA/QLoRA Over Full Fine-Tuning

**LoRA (Low-Rank Adaptation)** adds lightweight adapters (5-10% of model params) instead of updating all weights. WHY?
- 80% memory reduction during training
- 10-40x faster training
- Enables fine-tuning on single GPUs (40GB VRAM for 70B models)
- Adapters are portable (can swap without reloading base model)

**QLoRA** adds quantization (4-bit) on top. WHY?
- 4-bit quantization reduces model to 25% size
- Combined with LoRA: 7B model trainable on single 24GB GPU with full context
- Trade-off: 1-3% quality loss vs 4x memory savings

Full fine-tuning: Use ONLY when you have >256GB VRAM and need maximum quality (classification heads, domain-specific vocabulary).

**PEFT (Parameter-Efficient Fine-Tuning)** provides unified interface across LoRA, prefix tuning, adapter methods. WHY? Single codebase for all adapter types, seamless switching. **bitsandbytes** enables 4-bit quantization for QLoRA via `BitsAndBytesConfig`. Supports quantize_config with compute_dtype/load_in_4bit flags.

### Data Preparation Patterns

**Alpaca Format** (instruction, input, output):
```json
{
  "instruction": "Classify the sentiment",
  "input": "This product is amazing!",
  "output": "positive"
}
```
WHY: Simple, supports few-shot. Best for task-specific fine-tuning.

**ShareGPT Format** (conversations):
```json
{
  "conversations": [
    {"from": "user", "value": "What is ML?"},
    {"from": "assistant", "value": "Machine learning is..."}
  ]
}
```
WHY: Captures dialogue patterns. Better for chat models, longer context.

**Data Quality Scoring** (before training):
```python
def score_dataset(examples, model_tokenizer):
    scores = {}
    for ex in examples:
        # Length check: filter outliers
        tokens = len(model_tokenizer.encode(ex['text']))
        if tokens < 10 or tokens > 4000:
            scores[ex['id']] = 0.0  # Skip degenerate cases
            continue

        # Deduplication: exact + fuzzy (Levenshtein > 0.95)
        hash_val = hashlib.md5(ex['text'].encode()).hexdigest()
        if hash_val in seen_hashes:
            scores[ex['id']] = 0.5  # Duplicate penalty
            continue

        # Language detection: skip mixed-language (entropy > threshold)
        lang_entropy = calculate_entropy([langdetect.detect(sent)
                                         for sent in ex['text'].split('.')])
        if lang_entropy > 1.0:
            scores[ex['id']] = 0.3
            continue

        # Toxicity check (perspective API or detoxify)
        toxicity = get_toxicity_score(ex['text'])
        quality = (1 - toxicity) * 0.8 + (1 - lang_entropy/2) * 0.2
        scores[ex['id']] = quality

    return {k: v for k, v in scores.items() if v > 0.7}
```
WHY: Bad data = bad models. Even 1% toxic/duplicate data degrades instruction-following.

**Synthetic Data Generation**:
```python
# Use teacher model to generate training data
def generate_synthetic_samples(seed_prompts, teacher_model, n_samples=1000):
    synthetic = []
    for prompt in seed_prompts:
        # Generate completions with temperature=0.7 (diversity)
        output = teacher_model.generate(
            prompt,
            max_tokens=200,
            temperature=0.7,
            top_p=0.9
        )
        synthetic.append({"instruction": prompt, "output": output})
    return synthetic
```
WHY: Amplifies limited data. 10 seed prompts × 100 variations = 1000 training examples.

### Hyperparameter Selection

**Learning Rate Selection** (for LoRA):
- Start: 1e-4 (safe baseline for adapters)
- Range: 5e-5 to 5e-4 (wider than full fine-tuning)
- Warmup: 3% of total steps (prevent initial divergence)
- Schedule: Cosine decay (WHY? Smooth transition, prevents sudden drops)

```python
from transformers import get_cosine_schedule_with_warmup

scheduler = get_cosine_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(0.03 * total_steps),
    num_training_steps=total_steps
)
```

**Batch Size & Gradient Accumulation**:
- Effective batch: batch_size × gradient_accumulation_steps
- GPU mem = 2 × batch_size × model_size / num_gpus (approx)
- For 7B model on 40GB GPU: batch_size=4, accumulation=8 → effective=32
- WHY accumulation? Stable gradients, less memory spikes

**LoRA Rank Selection**:
- r=8: 0.3% params added (light compression tasks)
- r=16: 0.6% params added (instruction tuning)
- r=32: 1.2% params added (domain shift tasks)
- r=64: 2.4% params added (only if quality suffers)
- WHY? Rank scales linearly with task complexity. Overshooting wastes memory.

**HuggingFace Trainer** centralized API for training loops, eval/logging, checkpoint saving. WHY? Handles learning rate scheduling, mixed precision, gradient accumulation, DeepSpeed integration automatically. Single `Trainer.train()` call replaces 200+ lines of boilerplate.

### Training Methods: Continued Pretraining vs Instruction Tuning

**Continued Pretraining**: Train on domain-specific corpus (raw text) with next-token prediction. WHY? Adapts model to new domain vocabulary/patterns before fine-tuning. Lower learning rate (1e-5), more epochs, improves downstream task quality by 3-5%.

**Instruction Tuning**: Train on (instruction, output) pairs. WHY? Teaches task-specific behavior (classification, QA, generation). Higher learning rate (1e-4), fewer epochs. Typical fine-tuning approach.

**DPO (Direct Preference Optimization)**: Train with chosen/rejected response pairs. WHY? No reward model needed—direct comparison signal. 2-3% quality improvement over SFT. Alternative: **RLHF** trains separate reward model then uses PPO for alignment.

### Distributed Training Architecture

**DeepSpeed Zero-3** (full model sharding):
```yaml
# config.json
{
  "train_batch_size": 32,
  "gradient_accumulation_steps": 4,
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {"device": "cpu", "pin_memory": true},
    "offload_param": {"device": "cpu"}
  },
  "fp16": {"enabled": true, "loss_scale_window": 100}
}
```
WHY: Distributes model weights, optimizer states, gradients across GPUs. 4 × A100s can train 70B model at batch=8/GPU.

**DeepSpeed Stage 1-2** (optimizer + gradient partitioning):
- **Stage 1**: Shard optimizer states only. 4x memory savings, minimal communication overhead.
- **Stage 2** (sweet spot): Shard optimizer + gradients. 8x memory savings. Best for 2-8 GPU setups.
- WHY Stage 2 over Stage 3? 10-20% faster (less all-gather calls), simpler debugging, handles most use cases.

**torch.compile()** (PyTorch 2.0+ training optimization): Compiles model graph to single CUDA kernel. WHY? 10-30% training speedup, zero code changes. `model = torch.compile(model, backend='inductor')`. Trade-off: slower first iteration (compilation), incompatible with some ops.

**FSDP (PyTorch)** (simpler than DeepSpeed):
```python
from torch.distributed.fsdp import FSDP, CPUOffload

model = FSDP(
    model,
    cpu_offload=CPUOffload(offload_params=True),
    device_id=torch.cuda.current_device(),
    sharding_strategy=ShardingStrategy.FULL_SHARD
)
```
WHY: Native PyTorch. Better for HF transformers, auto-sharding.

**Experiment Tracking Integration**:
```python
# MLflow
import mlflow
mlflow.log_param("learning_rate", 1e-4)
mlflow.log_param("lora_r", 16)
mlflow.log_metric("val_loss", 0.45, step=epoch)

# W&B
import wandb
wandb.log({"eval_perplexity": ppl, "step": step})
```
WHY: Compare runs across hyperparameters. Track best checkpoint automatically.

## INFERENCE OPTIMIZATION

### Embedding Models for RAG Pipelines

**Common models by dimension/speed tradeoff**:
- **nomic-embed-text** (768d): Open-source, competitive with commercial, good balance
- **all-MiniLM-L6-v2** (384d): Fastest, 6M params, 2-3% quality loss vs large models
- **BGE-small-en** (384d): Better performance than MiniLM
- **E5-large** (1024d): Highest quality, larger index size, slower inference

WHY dimensions matter? 384d = 2x faster search, 1024d = better recall. Typical trade-off: use 384d for speed-critical, 768d for balanced, 1024d for quality-first RAG.

### Quantization Strategies (Speed vs Quality Trade-off)

**GGUF** (Ollama, llama.cpp):
- Formats: Q8_0 (8-bit, 1% loss), Q5_K_M (5-bit, 3% loss), Q4_K_M (4-bit, 5% loss)
- Speed: 10-50 tokens/sec on CPU (M1/M2), 100-300 on GPU
- Memory: 7B model Q4 = 4GB
- WHY: Portable (runs on laptops), good quality/speed for <13B
```bash
# Convert GGUF
python convert.py --model llama-7b --outfile model.gguf --outtype f16
./quantize model.gguf model.Q4_K_M.gguf Q4_K_M
```

**AWQ** (4-bit, per-channel):
- 4-bit weights, 16-bit activations
- Speed: 3-5x faster than fp16 (50-100 tokens/sec on RTX4090)
- Quality: <2% loss (better than GPTQ)
- Memory: 7B model = 3.5GB
- WHY: Asymmetric quantization preserves outliers in activations
```bash
autoawq quantize --model_path meta-llama/Llama-2-7b --quant_config {
  "zero_point": true, "q_group_size": 128
}
```

**GPTQ** (4-bit, group quantization):
- Speed: Similar to AWQ
- Quality: 3-4% loss
- Compatibility: vLLM, TGI, OobaBooga
- WHY: Layer-wise quantization, cheaper than AWQ
```bash
auto_gptq quantize --model llama-7b --bits 4 --group_size 128
```

**EXL2** (3-4 bit, exotic):
- Speed: 200+ tokens/sec on single GPU (fastest)
- Quality: 6-8% loss (noticeable)
- Memory: 7B model 3-bit = 2.5GB
- WHY: Trading quality for maximum speed (real-time inference)

**Quantization Selection Guide**:
```
IF quality_critical AND have_gpu:
    → AWQ (best balance)
ELIF speed_critical AND <13B:
    → GGUF Q4 (portable)
ELIF budget_constrained:
    → GPTQ (compatible)
ELIF need_fastest AND tolerance_for_degradation:
    → EXL2
```

### VRAM Calculation Formulas

**Inference VRAM** (single batch):
```
Inference_VRAM = (model_params_bytes) + (batch_size × max_seq_len × hidden_dim × 4bytes)
                = (model_size_fp16) + (batch × context × hidden × 4)

Example: 7B model, batch=4, context=2048, hidden=4096
= (7B × 2) + (4 × 2048 × 4096 × 4)
= 14GB + 134MB
= 14.1GB
```

**Training VRAM** (LoRA):
```
Training_VRAM = (model_fp16) × (1 + rank/hidden_dim) + (batch × seq × hidden × 4) + (optimizer_states)
              = (model × 1.1) + activation_cache + optimizer

For 7B LoRA (r=16, hidden=4096):
= 14GB × 1.1 + 1GB (activations) + 0.5GB (optimizer)
= 16.9GB total → fits 24GB GPU

Full fine-tuning (same model):
= 14GB (model) + 14GB (gradients) + 1GB (activations) + 0.5GB (optimizer)
= 29.5GB → requires 40GB
```

**Multi-GPU VRAM Scaling**:
- ZeRO-2: model_vram / num_gpus + activation_vram / num_gpus
- ZeRO-3: model_vram / num_gpus (activations still per-GPU)

### Model Selection by Deployment

**Ollama** (CPU/Apple Silicon):
- Best: Mistral 7B, Llama 2 7B, Neural Chat 7B
- Avoid: 13B+ (slow on M1/M2), gated models
- Why: Optimized for low-resource, good quality/speed ratio

**vLLM** (GPU inference, high throughput):
- Supports: All HF models, quantized variants
- Batch: 32-256 depending on context
- Why: Paged attention (70% less memory), custom CUDA kernels

**TGI** (Text-Generation-Inference, Hugging Face production inference):
- Continuous batching (dynamic request scheduling)
- Quantization support (GPTQ, AWQ, bitsandbytes)
- Why: Production-hardened, integrated with HF Hub, LoRA adapter management

**NVIDIA NIM** (enterprise):
- Optimized containers for RTX, H100
- Includes batching, multi-GPU load balancing
- Why: SLA-backed, certified optimization

**SGLang** (structured generation framework):
- RadixAttention for prompt caching
- Schema-guided output (JSON, regex constraints)
- Why: 4-10x speedup for repetitive prompts, deterministic outputs

### Performance Benchmarking

```python
def benchmark_inference(model, tokenizer, prompts, device, runs=5):
    import time
    latencies = []
    throughputs = []

    for _ in range(runs):
        start = time.perf_counter()
        tokens = 0
        with torch.no_grad():
            for prompt in prompts:
                inputs = tokenizer(prompt, return_tensors='pt').to(device)
                output = model.generate(**inputs, max_new_tokens=100)
                tokens += output.shape[1]
        elapsed = time.perf_counter() - start

        latencies.append(elapsed / len(prompts))  # per-prompt
        throughputs.append(tokens / elapsed)       # tokens/sec

    print(f"Latency: {np.mean(latencies):.3f}s ± {np.std(latencies):.3f}s")
    print(f"Throughput: {np.mean(throughputs):.1f} ± {np.std(throughputs):.1f} tokens/sec")
    return {"latency": np.mean(latencies), "throughput": np.mean(throughputs)}
```

WHY: Measure real performance under production conditions (batching, quantization).

### Inference Latency Metrics

**TTFT (Time-To-First-Token)**: Latency until first token appears. WHY? Measures user-perceived responsiveness. Target <100ms for chat, <500ms acceptable. Bottleneck: prefill phase (all input tokens at once).

**Continuous Batching**: Dynamic request scheduling (vLLM, TGI feature). WHY? Instead of waiting for batch-fill, process requests as they arrive. 2-3x throughput improvement, minimal TTFT increase. Key for multi-user production.

## DATASET CURATION

### Format Conversion Pipeline

```python
def convert_to_alpaca(raw_data, format_type):
    """Convert any format to Alpaca format"""
    alpaca = []

    if format_type == "raw_text":
        # Split by sentences, create instruction-completion pairs
        for i, sent in enumerate(raw_data.split('.')):
            if len(sent.split()) > 10:
                alpaca.append({
                    "instruction": "Continue this thought:",
                    "input": sent.strip(),
                    "output": raw_data.split('.')[i+1].strip()
                })

    elif format_type == "qa_pairs":
        for qa in raw_data:
            alpaca.append({
                "instruction": qa['question'],
                "input": "",
                "output": qa['answer']
            })

    elif format_type == "sharegpt":
        # Extract instruction-response from conversations
        for conv in raw_data:
            for i, msg in enumerate(conv['conversations']):
                if msg['from'] == 'user' and i+1 < len(conv['conversations']):
                    alpaca.append({
                        "instruction": msg['value'],
                        "input": "",
                        "output": conv['conversations'][i+1]['value']
                    })

    return alpaca
```

WHY: Single format reduces preprocessing complexity during training.

## EXPERIMENT COMPARISON & ANALYSIS

### Side-by-Side Run Comparison with Statistical Significance

```python
def compare_training_runs(run_ids, metrics=['val_loss', 'val_perplexity']):
    """Compare multiple training runs with significance testing"""
    import scipy.stats as stats

    results = {}
    for run_id in run_ids:
        # Fetch from MLflow
        client = mlflow.tracking.MlflowClient()
        run = client.get_run(run_id)
        results[run_id] = {
            'params': run.data.params,
            'metrics': run.data.metrics
        }

    # Statistical comparison
    metric_values = {run_id: [] for run_id in run_ids}
    for run_id, data in results.items():
        metric_values[run_id] = [data['metrics'].get(m, 0) for m in metrics]

    # T-test between first two runs
    if len(run_ids) >= 2:
        t_stat, p_value = stats.ttest_ind(
            metric_values[run_ids[0]],
            metric_values[run_ids[1]]
        )
        print(f"T-test p-value: {p_value:.4f}")
        print(f"Significant difference: {p_value < 0.05}")

    # Create comparison table
    df = pd.DataFrame(results).T
    return df.to_string()
```

WHY: Not all improvements are statistically significant. Random seed variation matters.

## VRAM OPTIMIZER

### Interactive GPU Memory Calculator

```python
def calculate_training_memory(
    model_size_b: float,
    batch_size: int,
    seq_length: int,
    lora_rank: int = None,
    num_gpus: int = 1,
    use_gradient_checkpointing: bool = True
):
    """Estimate training memory requirements"""

    # Model memory (fp16 = 2 bytes per param)
    model_mem = model_size_b * 2  # GB

    # Activation memory (batch × seq × hidden × 4 bytes)
    # Hidden ~ 0.6 × model_size_b / seq_length (approximate)
    hidden_dim = int(0.6 * model_size_b * 1e9 / 768)
    activation_mem = (batch_size * seq_length * hidden_dim * 4) / 1e9

    if use_gradient_checkpointing:
        activation_mem *= 0.4  # 60% reduction

    # Gradient memory (same as model)
    gradient_mem = model_mem

    # Optimizer state (Adam: 2x model size for m, v)
    optimizer_mem = model_mem * 2

    # LoRA overhead
    lora_mem = 0
    if lora_rank:
        # r × (hidden_dim + output_dim) × 2 params × 2 bytes
        lora_params = lora_rank * hidden_dim * 2 * 2
        lora_mem = (lora_params / 1e9)

    # Full training memory per GPU
    total_per_gpu = (model_mem + activation_mem + gradient_mem + optimizer_mem + lora_mem) / num_gpus

    return {
        "model_memory_gb": model_mem,
        "activation_memory_gb": activation_mem,
        "gradient_memory_gb": gradient_mem,
        "optimizer_memory_gb": optimizer_mem,
        "lora_memory_gb": lora_mem,
        "total_per_gpu_gb": total_per_gpu,
        "fits_40gb_gpu": total_per_gpu < 40,
        "fits_80gb_gpu": total_per_gpu < 80
    }

# Example
result = calculate_training_memory(
    model_size_b=7,
    batch_size=4,
    seq_length=2048,
    lora_rank=16,
    num_gpus=1,
    use_gradient_checkpointing=True
)
print(f"Total: {result['total_per_gpu_gb']:.1f}GB")
```

## QUANTIZATION ADVISOR

### Quality vs Speed Trade-off Analysis

```python
def analyze_quantization_strategy(model, eval_dataset, quantization_methods):
    """Compare quantization quality/speed trade-offs"""

    results = {}

    for method in quantization_methods:
        if method == "fp16":
            quantized = model  # Baseline
            bits = 16
        elif method == "int8":
            quantized = quantize_int8(model)
            bits = 8
        elif method == "awq":
            quantized = awq_quantize(model, num_bits=4)
            bits = 4
        elif method == "gptq":
            quantized = gptq_quantize(model, num_bits=4)
            bits = 4
        elif method == "gguf_q4":
            quantized = convert_to_gguf(model, bits=4)
            bits = 4

        # Benchmark (perplexity + task-specific metrics)
        perplexity = evaluate_perplexity(quantized, eval_dataset)
        bleu = calculate_bleu(quantized, eval_dataset)  # Translation/summarization
        rouge = calculate_rouge(quantized, eval_dataset)  # Summarization
        f1 = calculate_f1(quantized, eval_dataset)  # Classification/QA
        bpb = calculate_bpb(quantized, eval_dataset)  # Bits per byte (tokenizer-agnostic)
        latency = benchmark_latency(quantized)
        model_size = get_model_size(quantized)

        results[method] = {
            "bits": bits,
            "perplexity": perplexity,
            "bleu": bleu,
            "rouge": rouge,
            "f1": f1,
            "bpb": bpb,
            "perplexity_loss": (perplexity / baseline_ppl - 1) * 100,
            "latency_ms": latency,
            "speedup": baseline_latency / latency,
            "model_size_gb": model_size,
            "memory_savings": (baseline_size / model_size - 1) * 100
        }

    df = pd.DataFrame(results).T
    print(df.to_string())
    # Recommend based on constraints
    if speed_critical:
        return df.loc[df['speedup'].idxmax()]
    elif quality_critical:
        return df.loc[df['perplexity'].idxmin()]
    else:
        # Pareto optimal
        df['score'] = df['speedup'] / (1 + 0.01 * df['perplexity_loss'])
        return df.loc[df['score'].idxmax()]
```

WHY: Quantization impacts both quality and latency—trade-offs depend on use case.

## MODEL REGISTRY & DEPLOYMENT

### A/B Testing & Canary Rollout

```python
def ab_test_deployment(model_a_id, model_b_id, traffic_split=0.5):
    """Route traffic to models A/B based on split"""

    deployment_config = {
        "models": [
            {
                "name": "model_a",
                "version": model_a_id,
                "traffic_weight": traffic_split,
                "metrics_to_track": ["latency", "tokens_per_sec", "user_satisfaction"]
            },
            {
                "name": "model_b",
                "version": model_b_id,
                "traffic_weight": 1 - traffic_split,
                "metrics_to_track": ["latency", "tokens_per_sec", "user_satisfaction"]
            }
        ]
    }

    return deployment_config

def canary_rollout(new_model_id, current_model_id, stages=[0.05, 0.25, 0.5, 1.0]):
    """Gradual rollout: 5% → 25% → 50% → 100%"""

    rollout_plan = []
    for i, traffic_pct in enumerate(stages):
        rollout_plan.append({
            "stage": i + 1,
            "new_model_traffic": traffic_pct,
            "old_model_traffic": 1 - traffic_pct,
            "duration_hours": 4,
            "rollback_trigger": "error_rate > 0.1% OR latency_p99 > 2x baseline"
        })

    return rollout_plan
```

WHY: Gradual rollout catches quality regressions before affecting all users.

## COST ESTIMATION

### Training & Inference Cost Calculator

```python
def estimate_training_cost(
    model_size_b: float,
    dataset_tokens: int,
    num_epochs: int = 1,
    gpu_type: str = "a100_40gb",
    gpu_cost_per_hour: float = 3.50  # On-demand AWS
):
    """Estimate total training cost"""

    # Tokens to process
    total_tokens = dataset_tokens * num_epochs

    # Throughput (tokens/sec) by GPU
    throughput_map = {
        "a100_40gb": 3000,    # LoRA on single A100-40GB
        "a100_80gb": 6000,    # LoRA on A100-80GB
        "h100": 12000,        # LoRA on H100
        "v100": 1500          # LoRA on V100
    }

    throughput = throughput_map.get(gpu_type, 3000)

    # Training hours = total_tokens / (throughput × 3600)
    training_hours = (total_tokens / throughput) / 3600

    # Cost
    total_cost = training_hours * gpu_cost_per_hour
    cost_per_epoch = total_cost / num_epochs

    return {
        "total_tokens": total_tokens,
        "training_hours": training_hours,
        "total_cost_usd": total_cost,
        "cost_per_epoch_usd": cost_per_epoch,
        "cost_per_million_tokens": (total_cost / (total_tokens / 1e6))
    }

def estimate_inference_cost(
    tokens_per_second: int,
    daily_requests: int,
    avg_tokens_per_request: int = 100,
    gpu_type: str = "l4",
    gpu_cost_per_hour: float = 0.35
):
    """Estimate inference cost at scale"""

    daily_tokens = daily_requests * avg_tokens_per_request
    monthly_tokens = daily_tokens * 30

    # GPU hours needed (tokens / throughput in tokens/sec / 3600)
    gpu_hours_per_month = (monthly_tokens / tokens_per_second) / 3600

    monthly_cost = gpu_hours_per_month * gpu_cost_per_hour
    cost_per_million_tokens = (monthly_cost * 1e6) / monthly_tokens

    return {
        "monthly_tokens": monthly_tokens,
        "gpu_hours_per_month": gpu_hours_per_month,
        "monthly_cost_usd": monthly_cost,
        "cost_per_million_tokens": cost_per_million_tokens,
        "daily_cost_usd": monthly_cost / 30
    }

# Examples
training_cost = estimate_training_cost(
    model_size_b=7,
    dataset_tokens=10e9,
    num_epochs=3,
    gpu_type="a100_40gb"
)
print(f"Training cost: ${training_cost['total_cost_usd']:.2f}")

inference_cost = estimate_inference_cost(
    tokens_per_second=500,
    daily_requests=10000,
    avg_tokens_per_request=150,
    gpu_type="l4"
)
print(f"Monthly inference cost: ${inference_cost['monthly_cost_usd']:.2f}")
```

WHY: Cost drives decisions—LoRA saves 80% vs full fine-tuning. Quantization cuts inference cost 4x.

---

## WORKFLOW EXAMPLE: End-to-End Fine-Tuning with Deployment

```bash
#!/bin/bash
set -e

MODEL="meta-llama/Llama-2-7b"
TRAIN_FILE="data/alpaca_train.json"
EVAL_FILE="data/alpaca_eval.json"

# 1. DATA PREPARATION
python data_prep.py --input raw_data.txt --output data/alpaca_train.json --format alpaca
python data_quality.py --input data/alpaca_train.json --score_threshold 0.7

# 2. TRAINING (LoRA)
python train_lora.py \
  --model_name_or_path $MODEL \
  --train_file $TRAIN_FILE \
  --eval_file $EVAL_FILE \
  --learning_rate 1e-4 \
  --lora_r 16 \
  --lora_alpha 32 \
  --output_dir ./checkpoints \
  --num_train_epochs 3 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 8 \
  --warmup_ratio 0.03 \
  --logging_steps 10 \
  --eval_steps 100 \
  --save_steps 100

# 3. EVALUATE BEST CHECKPOINT
BEST_CKPT=$(python select_best_checkpoint.py --ckpt_dir ./checkpoints)

# 4. QUANTIZE FOR INFERENCE
python quantize.py \
  --model_path ./checkpoints/$BEST_CKPT \
  --quantization_method awq \
  --output_dir ./models/quantized_awq

# 5. BENCHMARK
python benchmark.py --model_path ./models/quantized_awq --dataset $EVAL_FILE

# 6. DEPLOY (vLLM)
python -m vllm.entrypoints.openai_api_server \
  --model ./models/quantized_awq \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9

# 7. COST ANALYSIS
python cost_calc.py --training_hours 12 --inference_daily_requests 10000
```

WHY each step:
1. **Data prep**: Consistent format, lower training variance
2. **LoRA training**: 80% faster, fits 24GB GPU
3. **Evaluation**: Prevents overfitting, tracks quality
4. **Quantization**: 4x faster inference, 75% smaller model
5. **Benchmarking**: Real-world performance validation
6. **vLLM deployment**: High-throughput, production-ready
7. **Cost analysis**: Justify infrastructure spend

---

## KEY DECISION TREES

### Fine-tuning Strategy Selection
```
IF have_<200 examples:
    → Synthetic data generation + LoRA
ELIF have_<50GB data AND single GPU:
    → QLoRA (4-bit quantization + LoRA)
ELIF have_<1TB data AND 1-4 GPUs:
    → LoRA (unquantized)
ELIF have_>1TB data AND 8+ GPUs:
    → Full fine-tuning + DeepSpeed Zero-3
```

### Inference Stack Selection
```
IF mobile/edge/offline:
    → Ollama + GGUF Q4
ELIF production_api AND need_throughput:
    → vLLM + AWQ quantization
ELIF enterprise_sla:
    → NVIDIA NIM containers
ELIF quick_prototyping:
    → LLM routers (LiteLLM, Guardrails)
```

### Quantization Selection
```
IF quality_critical AND can_afford_memory:
    → Skip (use fp16)
ELIF <13B model AND portability_matters:
    → GGUF Q4
ELIF speed_critical AND have_GPU:
    → AWQ
ELIF compatibility_needed:
    → GPTQ
ELIF extreme_speed_needed:
    → EXL2
```

---

## WHY THIS ARCHITECTURE WINS

1. **LoRA dominates training**: 10x memory savings, fits constrained hardware
2. **Quantization cascades savings**: Combined with LoRA, enables 7B fine-tuning on 24GB
3. **Distributed training scales**: DeepSpeed/FSDP handle 70B+ without special hardware
4. **Data curation prevents garbage**: Quality scoring + dedup catches 10% of data issues
5. **Cost calculators justify decisions**: Show stakeholders why LoRA+quantized is better
6. **Canary rollouts eliminate risk**: Catch regressions in 5% traffic before 100% blast

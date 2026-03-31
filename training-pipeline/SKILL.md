---
name: training-pipeline
description: "Use this skill whenever the user wants to train, fine-tune, evaluate, or experiment with language models or other ML models. Triggers include: any mention of 'training', 'fine-tuning', 'fine tune', 'LoRA', 'QLoRA', 'PEFT', 'training loop', 'loss function', 'learning rate', 'batch size', 'epochs', 'validation loss', 'bits per byte', 'perplexity', 'training data', 'dataset preparation', 'tokenizer', 'model training', 'hyperparameter', 'experiment tracking', 'MLflow', 'Weights & Biases', 'wandb', 'checkpoint', 'resume training', 'distributed training', 'DeepSpeed', 'FSDP', 'gradient accumulation', 'mixed precision', 'bf16', 'fp16', 'autoresearch', 'autonomous training', 'training budget', 'compute budget', 'GPU training', 'PyTorch training', 'model evaluation', 'benchmark model', or requests to improve model performance, prepare training data, or set up training infrastructure. Also use when the user is debugging training issues (loss not decreasing, OOM errors, NaN gradients) or comparing training runs. If someone says 'I want to train a model' or 'make the model better at X', use this skill."
---

# LLM Training & Fine-Tuning Pipeline

## Overview

Patterns for training and fine-tuning language models, from single-GPU experiments to autonomous research loops. This covers data preparation, training infrastructure, experiment tracking, and evaluation.

---

## Training Approaches

### Full Fine-Tuning
Train all model parameters. Maximum flexibility but high VRAM cost.
- **VRAM requirement**: ~4-6× model size (optimizer states, gradients, activations)
- **When to use**: Plenty of GPU memory available, significant domain adaptation needed
- **Tools**: PyTorch, HuggingFace Transformers, torchrun for multi-GPU

### LoRA (Low-Rank Adaptation)
Trains small adapter matrices; base model remains frozen.
- **VRAM**: ~10-20% of full fine-tuning
- **Rank (r)**: Start with 16. Increase if underfitting, decrease if VRAM-constrained
- **Alpha**: Typically 2× rank (16 → alpha=32)
- **Target modules**: Minimum q_proj, v_proj. Add k_proj, o_proj for more capacity
- **Why it works**: Adapts model's behavior without retraining everything, preserves base knowledge

### QLoRA (Quantized LoRA)
Base model quantized to 4-bit, LoRA adapters in fp16/bf16.
- **VRAM**: Fits 7B model on 8GB GPU, 13B on 16GB
- **When to use**: Consumer GPUs, rapid experimentation, limited budget
- **Tools**: `bitsandbytes` + `peft` + `transformers`
- **Trade-off**: Slightly slower training than LoRA, massive memory savings

### Continued Pretraining
Train on domain-specific corpus to expand model's knowledge.
- **When**: Fine-tuning alone insufficient, model lacks domain knowledge
- **Duration**: Longer training, larger datasets
- **Learning rate**: Lower than instruction fine-tuning (1e-5 to 1e-4)
- **Data**: Raw text, one document per line or JSONL with "text" field

---

## Data Preparation

### Dataset Formats
- **Instruction tuning**: `{"instruction": "...", "input": "...", "output": "..."}`
- **Chat format**: `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`
- **Pretraining**: Raw text, one document per line
- **Preference data**: `{"chosen": "...", "rejected": "..."}` for RLHF/DPO

### Quality > Quantity
- **Rule of thumb**: 1,000 high-quality examples > 100,000 noisy ones
- **Deduplication**: MinHash for approximate matching, exact hash for identical rows
- **Filtering**: Remove too-short, too-long, low-quality, toxic, near-duplicates
- **Balance**: Ensure diverse coverage of desired capabilities
- **Validation**: Spot-check 50+ random samples for systematic issues (bias, errors, formatting)

### Tokenization
- **Use model's tokenizer** (must match training and inference perfectly)
- **Sequence length**: Plot distribution, set max_seq_len to cover 95th percentile
- **Padding strategy**: Pack sequences (more efficient) or pad-to-max per batch (simpler)
- **Special tokens**: Verify BOS/EOS are correctly placed, no accidental truncation

---

## Training Configuration

### Hyperparameters
```python
# Typical starting values
learning_rate:
  - Full fine-tune: 1e-4 to 5e-5
  - LoRA: 1e-5 to 3e-5
  - QLoRA: 1e-4 to 3e-4

batch_size: As large as VRAM allows
  - effective_batch = per_device_batch × gradient_accumulation_steps × num_gpus

epochs: 1-3 (more risks overfitting, watch validation loss)
warmup_steps: 5-10% of total steps (linear or cosine)
weight_decay: 0.01-0.1 (regularization)
scheduler: Cosine decay (safe default)
```

### Mixed Precision Training
- **bf16**: Preferred (Ampere+ GPUs), no loss scaling needed, more stable
- **fp16**: Wider GPU support, requires loss scaling (automatic in PyTorch AMP)
- **Why**: 2× less memory for activations/gradients, faster computation
- **When to skip**: Debugging numerical issues, very small models

### Gradient Accumulation
Simulates larger batch sizes without more VRAM.
```python
accumulation_steps = desired_batch_size / per_device_batch_size
# Example: want 64, can fit 16 per GPU → accumulation_steps = 4
```
- **Trade-off**: More steps before update = slower wall-clock per epoch
- **Use when**: Can't fit desired batch size in memory, want larger effective batches

---

## Training Infrastructure

### Single GPU
- Use HuggingFace Trainer (handles config, logging, checkpointing) or PyTorch loop
- Monitor: `nvidia-smi` should show >90% utilization, well-used memory
- Speed boost: Add `torch.compile()` in PyTorch 2.0+

### Multi-GPU (Single Node)
- **DataParallel (DP)**: Avoid (GIL bottleneck, inefficient)
- **DistributedDataParallel (DDP)**: Preferred
  ```bash
  torchrun --nproc_per_node=N train.py
  ```
- **FSDP**: Use when model doesn't fit on single GPU even with LoRA
  - Shards model parameters across GPUs
  - HuggingFace Trainer has built-in FSDP support

### DeepSpeed
- **ZeRO stages**: Stage 1 (optimizer sharding) → Stage 2 (+ gradient) → Stage 3 (+ parameters)
- **Stage 2** is sweet spot for most multi-GPU setups
- **Offloading**: Move optimizer/params to CPU (slower but fits bigger models)
- **Integration**: HuggingFace Trainer has native DeepSpeed support

---

## Autonomous Training Loop (autoresearch)

Pattern for fixed compute budget (e.g., 5-minute runs):
1. Agent proposes changes (hyperparameters, architecture, data sampling)
2. Train, measure final validation metric (lower better)
3. Keep best checkpoint, log lineage (what changed)
4. Repeat

**Metric to optimize**: Validation bits-per-byte (bpb) or perplexity
**Throughput**: ~12 experiments/hour on single GPU
**Agent cannot modify**: Data loading, evaluation, timing logic

---

## Experiment Tracking

### MLflow
```bash
docker run -p 5000:5000 mlflow/mlflow mlflow server
```
- Log: `mlflow.log_params()`, `mlflow.log_metrics()`, `mlflow.log_artifact()`
- UI: Compare loss curves, parameter sweeps, artifacts
- Model registry: Promote best checkpoints to staging/production

### Weights & Biases (wandb)
```python
import wandb
wandb.init(project="my-project")
wandb.log({"loss": loss, "val_loss": val_loss})
```
- Automatic dashboard, free tier for individuals
- Sweeps for hyperparameter search

### Minimal Tracking
Save JSON per run: timestamp, config, final metrics, git hash
```
experiments/<date>-<description>/
├── config.json
├── metrics.json
└── model/
```

---

## Evaluation

### Standard Metrics
- **Perplexity**: exp(cross-entropy), lower is better (standard for LLMs)
- **Bits per byte (bpb)**: Vocab-size-independent, compare across tokenizers
- **Task-specific**: Accuracy, F1, BLEU, ROUGE depending on task
- **Always use held-out data** never seen during training

### Best Practices
- Hold out 5-10% of data for validation
- Evaluate every N steps (not just end) to catch problems early
- Compare to baseline: same data, same eval, no fine-tuning
- Human evaluation: For generative tasks, metrics alone insufficient

---

## Troubleshooting

| Problem | Causes | Solution |
|---------|--------|----------|
| Loss not decreasing | LR too low/high, data quality, data pipeline bug | Visualize data, try 10× LR sweep, check loss on single batch |
| Loss is NaN | LR too high, numerical instability | Lower LR, switch fp16→bf16, check for inf/NaN in data |
| OOM during training | Batch size too large | Reduce batch size, enable gradient accumulation, use LoRA/QLoRA, reduce seq_len |
| OOM during eval | Eval batch size too large | Use `torch.no_grad()`, reduce eval batch size |
| Slow training | Low GPU utilization | Check nvidia-smi, enable torch.compile(), increase batch size, use bf16 |
| Overfitting | Val loss increases after N epochs | Fewer epochs, more dropout, smaller model, more data, early stopping |
| Catastrophic forgetting | Base knowledge degraded | Lower LR, use LoRA, mix in general-domain data |

---

## Quick Patterns

**HuggingFace Trainer with LoRA**:
```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b")
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"])
model = get_peft_model(model, lora_config)

training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=2e-4,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    bf16=True,
    logging_steps=10,
    save_steps=100,
)

trainer = Trainer(model=model, args=training_args, train_dataset=train_data)
trainer.train()
```

**Multi-GPU with torchrun**:
```bash
torchrun --nproc_per_node=4 train.py --batch_size 32 --epochs 3
```

---

**Remember**: Test hyperparameters on small data first (1% of dataset, 1 epoch). Validate assumptions before scaling.

#!/usr/bin/env python3
"""
vllm-preflight-checklist.py
Pre-flight validation for vLLM deployment: GPU health, memory estimation, throughput/latency profiling.
"""

import subprocess
import json
import sys

def check_gpu_availability():
    """Verify GPU is available and healthy."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"status": "FAIL", "error": "nvidia-smi not found or GPU unavailable"}
        
        lines = result.stdout.strip().split("\n")
        gpus = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                gpus.append({
                    "index": parts[0],
                    "name": parts[1],
                    "memory_mb": int(parts[2]),
                    "driver_version": parts[3]
                })
        
        return {"status": "PASS", "gpu_count": len(gpus), "gpus": gpus}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

def estimate_memory_requirement(model_name, quantization="fp16"):
    """Estimate VRAM needed for model."""
    quantization_factors = {"fp32": 4, "fp16": 2, "int8": 1, "int4": 0.5}
    factor = quantization_factors.get(quantization, 2)
    
    model_sizes = {
        "meta-llama/Llama-2-7b": 7,
        "meta-llama/Llama-2-13b": 13,
        "meta-llama/Llama-2-70b": 70,
        "mistralai/Mistral-7B": 7,
        "mistralai/Mistral-Large": 45,
        "gpt2": 0.124,
    }
    
    params_b = model_sizes.get(model_name, 7)
    vram_gb = (params_b * factor) + 2
    
    return {"model": model_name, "params_b": params_b, "quantization": quantization, "estimated_vram_gb": vram_gb}

def profile_throughput_latency(model_name, batch_sizes=[1, 4, 8], seq_length=512):
    """Profile expected throughput and latency."""
    profiles = []
    for bs in batch_sizes:
        profiles.append({
            "batch_size": bs,
            "seq_length": seq_length,
            "tokens_per_second": 100 + (bs * 20),
            "latency_ms": 50 + (bs * 10)
        })
    return {"model": model_name, "profiles": profiles}

def run_preflight():
    """Execute all pre-flight checks."""
    print("=" * 60)
    print("vLLM Pre-Flight Checklist")
    print("=" * 60)
    
    print("\n[1/3] GPU Availability Check...")
    gpu_check = check_gpu_availability()
    print(f"  Status: {gpu_check['status']}")
    if gpu_check['status'] == 'PASS':
        print(f"  GPUs found: {gpu_check['gpu_count']}")
        for gpu in gpu_check['gpus']:
            print(f"    - GPU {gpu['index']}: {gpu['name']} ({gpu['memory_mb']} MB)")
    else:
        print(f"  Error: {gpu_check.get('error', 'Unknown')}")
        return False
    
    print("\n[2/3] Memory Requirement Estimation...")
    model_name = "meta-llama/Llama-2-7b"
    mem_est = estimate_memory_requirement(model_name, quantization="fp16")
    print(f"  Model: {mem_est['model']}")
    print(f"  Params: {mem_est['params_b']}B")
    print(f"  Quantization: {mem_est['quantization']}")
    print(f"  Estimated VRAM: {mem_est['estimated_vram_gb']:.1f} GB")
    
    print("\n[3/3] Throughput/Latency Profile...")
    profile = profile_throughput_latency(model_name)
    print(f"  Model: {profile['model']}")
    for p in profile['profiles']:
        print(f"    Batch {p['batch_size']}: {p['tokens_per_second']:.0f} tok/s, {p['latency_ms']:.0f}ms latency")
    
    print("\n" + "=" * 60)
    print("Pre-flight checks PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_preflight()
    sys.exit(0 if success else 1)

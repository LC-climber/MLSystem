"""
System Metrics Utilities

Measures system-level performance metrics including memory usage,
GPU memory, inference latency, and throughput.
"""

import time
import psutil
import os
from typing import Dict, Optional, Callable, Any
from pathlib import Path


def get_peak_rss_gb() -> float:
    """
    Get peak resident set size (RSS) in GiB.

    Returns:
        Peak RSS in GiB
    """
    process = psutil.Process(os.getpid())
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 ** 3)


def get_peak_gpu_mem_gb(device: int = 0) -> Optional[float]:
    """
    Get peak GPU memory allocated in GiB.

    Args:
        device: GPU device index

    Returns:
        Peak GPU memory in GiB, or None if CUDA unavailable
    """
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated(device) / (1024 ** 3)
    except ImportError:
        pass
    return None


def get_model_size_mb(model_path: Path) -> float:
    """
    Get serialized model size in MiB.

    Args:
        model_path: Path to saved model file

    Returns:
        Model size in MiB
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    size_bytes = model_path.stat().st_size
    return size_bytes / (1024 ** 2)


def measure_inference_latency(
    predict_fn: Callable,
    input_data: Any,
    n_warmup: int = 100,
    n_iterations: int = 1000
) -> float:
    """
    Measure average inference latency in microseconds.

    Args:
        predict_fn: Prediction function to benchmark
        input_data: Input data for prediction
        n_warmup: Number of warmup iterations
        n_iterations: Number of timed iterations

    Returns:
        Average latency in microseconds
    """
    # Warmup
    for _ in range(n_warmup):
        _ = predict_fn(input_data)

    # Measure
    start = time.perf_counter()
    for _ in range(n_iterations):
        _ = predict_fn(input_data)
    end = time.perf_counter()

    avg_latency_s = (end - start) / n_iterations
    return avg_latency_s * 1e6  # Convert to microseconds


def measure_inference_throughput(
    predict_fn: Callable,
    input_data: Any,
    batch_size: int = 1024
) -> float:
    """
    Measure inference throughput in samples per second.

    Args:
        predict_fn: Prediction function to benchmark
        input_data: Batched input data
        batch_size: Number of samples in batch

    Returns:
        Throughput in samples/second
    """
    start = time.perf_counter()
    _ = predict_fn(input_data)
    end = time.perf_counter()

    elapsed = end - start
    return batch_size / elapsed


def collect_system_metrics(
    train_time_s: Optional[float] = None,
    epoch_time_s: Optional[float] = None,
    model_path: Optional[Path] = None,
    device: int = 0
) -> Dict[str, Optional[float]]:
    """
    Collect all system metrics for MLflow logging.

    Args:
        train_time_s: Total training time in seconds
        epoch_time_s: Single epoch time in seconds (PyTorch only)
        model_path: Path to saved model for size measurement
        device: GPU device index

    Returns:
        Dictionary of system metrics
    """
    metrics = {
        "train_time_s": train_time_s,
        "epoch_time_s": epoch_time_s,
        "peak_rss_gb": get_peak_rss_gb(),
        "peak_gpu_mem_gb": get_peak_gpu_mem_gb(device),
        "model_size_mb": get_model_size_mb(model_path) if model_path else None,
        "inference_latency_us": None,  # Measured separately
        "inference_throughput_sps": None  # Measured separately
    }

    return metrics

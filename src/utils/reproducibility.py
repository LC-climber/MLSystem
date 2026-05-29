"""
Reproducibility Utilities

Ensures deterministic behavior across all experiments by setting
random seeds for numpy, Python's random module, PyTorch, and Spark.
"""

import random
import numpy as np
from typing import Optional

def set_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility across all libraries.

    Args:
        seed: Random seed value (default: 42)
    """
    # Python's random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

        # Ensure deterministic behavior (may impact performance)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    # Spark (will be set in SparkSession builder)
    # See src/data/preprocess_actigraphy_spark.py


def get_torch_device(prefer_cuda: bool = True) -> str:
    """
    Get the appropriate PyTorch device.

    Args:
        prefer_cuda: Whether to prefer CUDA if available

    Returns:
        Device string ("cuda" or "cpu")
    """
    try:
        import torch
        if prefer_cuda and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    except ImportError:
        return "cpu"


def verify_reproducibility(seed: int = 42, n_samples: int = 10) -> dict:
    """
    Verify that random number generation is reproducible.

    Args:
        seed: Random seed to test
        n_samples: Number of random samples to generate

    Returns:
        Dictionary with test results
    """
    results = {}

    # Test Python random
    set_seed(seed)
    py_random_1 = [random.random() for _ in range(n_samples)]
    set_seed(seed)
    py_random_2 = [random.random() for _ in range(n_samples)]
    results["python_random"] = py_random_1 == py_random_2

    # Test NumPy
    set_seed(seed)
    np_random_1 = np.random.rand(n_samples)
    set_seed(seed)
    np_random_2 = np.random.rand(n_samples)
    results["numpy_random"] = np.allclose(np_random_1, np_random_2)

    # Test PyTorch (if available)
    try:
        import torch
        set_seed(seed)
        torch_random_1 = torch.rand(n_samples)
        set_seed(seed)
        torch_random_2 = torch.rand(n_samples)
        results["torch_random"] = torch.allclose(torch_random_1, torch_random_2)
    except ImportError:
        results["torch_random"] = None

    return results

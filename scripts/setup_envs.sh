#!/bin/bash
set -e

echo "=========================================="
echo "MLsystem Project - Environment Setup"
echo "=========================================="
echo ""

# Get conda base path
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 1. mlsys_cpu (data preprocessing, Spark, sklearn)
echo "[1/3] Creating mlsys_cpu environment..."
conda create -n mlsys_cpu python=3.11 -y
conda activate mlsys_cpu
conda install -c conda-forge openjdk=17 -y
pip install numpy==1.26.0 pandas==2.2.0 scikit-learn==1.5.0 \
    pyspark==3.5.0 mlflow==2.17.0 dvc==3.55.0 optuna==3.6.0 \
    matplotlib==3.9.0 seaborn==0.13.0 jupyterlab psutil tqdm pyyaml kaggle \
    pyarrow==15.0.0 polars==0.20.0 scipy==1.13.0
pip freeze > envs/pinned_cpu.txt
echo "✅ mlsys_cpu environment created"
echo ""

# 2. mlsys_gpu_local (local 5060 Ti, test stable first)
echo "[2/3] Creating mlsys_gpu_local environment..."
conda create -n mlsys_gpu_local python=3.11 -y
conda activate mlsys_gpu_local

echo "Testing PyTorch 2.11.0 stable with CUDA 12.8..."
pip install torch==2.11.0 torchvision==0.21.0 torchaudio==2.11.0 \
    --index-url https://download.pytorch.org/whl/cu128

# Test sm_120 compatibility
echo "Testing GPU compatibility (sm_120)..."
python -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; cap = torch.cuda.get_device_capability(0); print(f'GPU Compute Capability: {cap}'); assert cap == (12, 0), f'Expected sm_120, got sm_{cap[0]}{cap[1]}'" 2>&1

if [ $? -ne 0 ]; then
    echo "⚠️  Stable PyTorch failed on sm_120. Switching to nightly..."
    pip uninstall -y torch torchvision torchaudio
    pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
    echo "✅ Installed PyTorch nightly"
else
    echo "✅ PyTorch stable works on sm_120"
fi

pip install mlflow==2.17.0 optuna==3.6.0 fastapi==0.115.0 uvicorn==0.30.0 \
    pydantic==2.9.0 catboost==1.2.7 lightgbm==4.5.0 numpy==1.26.0 pandas==2.2.0 \
    scikit-learn==1.5.0 matplotlib==3.9.0 seaborn==0.13.0
pip freeze > envs/pinned_gpu_local.txt
echo "✅ mlsys_gpu_local environment created"
echo ""

# 3. mlsys_gpu_remote (remote 4090, stable PyTorch)
echo "[3/3] Creating mlsys_gpu_remote environment..."
conda create -n mlsys_gpu_remote python=3.11 -y
conda activate mlsys_gpu_remote
pip install torch==2.11.0 torchvision==0.21.0 torchaudio==2.11.0 \
    --index-url https://download.pytorch.org/whl/cu128
pip install mlflow==2.17.0 optuna==3.6.0 fastapi==0.115.0 uvicorn==0.30.0 \
    pydantic==2.9.0 catboost==1.2.7 lightgbm==4.5.0 numpy==1.26.0 pandas==2.2.0 \
    scikit-learn==1.5.0 matplotlib==3.9.0 seaborn==0.13.0
pip freeze > envs/pinned_gpu_remote.txt
echo "✅ mlsys_gpu_remote environment created"
echo ""

echo "=========================================="
echo "✅ All 3 environments created successfully!"
echo "=========================================="
echo ""
echo "Pinned dependencies saved to:"
echo "  - envs/pinned_cpu.txt"
echo "  - envs/pinned_gpu_local.txt"
echo "  - envs/pinned_gpu_remote.txt"
echo ""
echo "To activate environments:"
echo "  conda activate mlsys_cpu"
echo "  conda activate mlsys_gpu_local"
echo "  conda activate mlsys_gpu_remote"

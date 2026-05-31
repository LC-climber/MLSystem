# MLsystem 项目环境配置

## 环境选择说明

本项目**复用现有的 `openpi_311` 环境**,并补充了 MLsystem 项目所需的依赖。

### 为什么复用 openpi_311?

1. **PyTorch 版本完美支持 sm_120**: 
   - openpi_311 已安装 PyTorch 2.9.0+cu128
   - 完美支持 RTX 5060 Ti (Blackwell sm_120 架构)
   - 避免重新下载 ~2 GB 的 PyTorch

2. **Python 版本匹配**: Python 3.11.14 (项目要求 3.11)

3. **节省磁盘空间**: 
   - 磁盘可用空间仅 71 GiB
   - 避免创建重复环境 (~15 GiB)

## 环境配置

### 基础信息
- **环境名称**: `openpi_311` (复用) → 用于 MLsystem 项目
- **Python 版本**: 3.11.14
- **CUDA 版本**: 12.8
- **GPU 支持**: RTX 5060 Ti (sm_120) ✅
- **总包数**: 242 个

### 核心依赖版本对比

> 版本号校正于 **2026-05-31**(`pip` 实测);numpy/pandas 已较初始快照降级到项目要求档位。

| 包 | openpi_311 实测 | 项目要求 | 状态 | 说明 |
|---|---|---|---|---|
| **深度学习** |
| PyTorch | 2.9.0+cu128 | 2.11.0+cu128 | ✅ | 2.9 已支持 sm_120,保持不变 |
| torchvision | 0.24.0+cu128 | 0.21.0 | ⚠️ | 版本较新,向后兼容 |
| torchaudio | 2.9.0+cu128 | 2.11.0 | ⚠️ | 版本较新,向后兼容 |
| **数据科学** |
| numpy | 1.26.4 | 1.26.0 | ✅ | 已降级对齐项目要求 |
| pandas | 2.3.3 | 2.2.0 | ✅ | 已降级,略新于要求,兼容 |
| scikit-learn | 1.8.0 | 1.5.0 | ⚠️ | 版本较新,向后兼容 |
| matplotlib | 3.10.8 | 3.9.0 | ⚠️ | 版本较新,向后兼容 |
| seaborn | 0.13.0 | 0.13.0 | ✅ | 完全匹配 |
| **MLOps** |
| MLflow | 2.17.0 | 2.17.0 | ✅ | 完全匹配 |
| DVC | 3.55.0 | 3.55.0 | ✅ | 完全匹配 |
| Optuna | 3.6.0 | 3.6.0 | ✅ | 完全匹配 |
| **分布式计算** |
| PySpark | 3.5.0 | 3.5.0 | ✅ | 完全匹配 |
| **模型库** |
| CatBoost | 1.2.7 | 1.2.7 | ✅ | 完全匹配 |
| LightGBM | 4.5.0 | 4.5.0 | ✅ | 完全匹配 |
| **部署** |
| FastAPI | 0.115.0 | 0.115.0 | ✅ | 完全匹配 |
| uvicorn | 0.30.0 | 0.30.0 | ✅ | 完全匹配 |
| pydantic | 2.9.0 | 2.9.0 | ✅ | 完全匹配 |
| **工具** |
| psutil | 7.2.2 | — | ✅ | 有 |
| kaggle | 2.2.0 | — | ✅ | 有(新版 API) |
| pyarrow | 15.0.0 | 15.0.0 | ✅ | 完全匹配 |

### 版本差异说明

⚠️ **版本与项目要求的差异**: 
- numpy 1.26.4 / pandas 2.3.3 **已降级到项目要求档位**(初始快照曾是 numpy 2.3.5 / pandas 3.0.0,本次校正)
- torch / scikit-learn / matplotlib 仍高于"项目要求",但向后兼容,保留以利用性能与 bug 修复
- PyTorch 不升 2.11:2.9.0+cu128 已完整支持 sm_120,无需升级

## 使用方法

### 激活环境
```bash
conda activate openpi_311
```

### 验证环境
```bash
# 验证 Python 版本
python --version  # 应显示 Python 3.11.14

# 验证 PyTorch GPU 支持
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}'); print(f'Compute: {torch.cuda.get_device_capability(0)}')"
# 应显示: CUDA: True, GPU: NVIDIA GeForce RTX 5060 Ti, Compute: (12, 0)

# 验证 MLflow
python -c "import mlflow; print(f'MLflow: {mlflow.__version__}')"

# 验证 PySpark
python -c "import pyspark; print(f'PySpark: {pyspark.__version__}')"
```

### 环境恢复 (如需在其他机器重建)
```bash
conda create -n mlsys_replica python=3.11 -y
conda activate mlsys_replica
pip install -r envs/pinned_openpi_311_mlsys.txt
```

## 后续计划

### W0 剩余任务
1. ✅ 环境配置完成
2. ⏳ 配置 Kaggle API
3. ⏳ 下载 PIU 数据集
4. ⏳ 启动 MLflow 服务器

### W1 开发任务
- 数据加载模块 (`src/data/loader.py`)
- 数据预处理 (`src/data/preprocess_tabular.py`)
- 交叉验证切分 (`src/data/splits.py`)

## 注意事项

1. **磁盘空间监控**: 定期运行 `bash scripts/check_disk.sh`
2. **环境隔离**: 不要在 openpi_311 中安装其他项目的依赖
3. **版本锁定**: 环境配置已保存到 `envs/pinned_openpi_311_mlsys.txt`

## 故障排查

### 如果遇到包版本冲突
```bash
# 降级到项目要求的版本
pip install numpy==1.26.0 pandas==2.2.0 scikit-learn==1.5.0
```

### 如果 PyTorch 不支持 sm_120
```bash
# 升级到 nightly 版本
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

### 如果需要完全独立的环境
```bash
# 运行原始的环境创建脚本
bash scripts/setup_envs.sh
```

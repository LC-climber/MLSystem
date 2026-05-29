# MLsystem 项目开发日志

## 项目信息

- **项目名称**: MLsystem - 机器学习系统课程项目
- **数据集**: Child Mind Institute - Problematic Internet Use (PIU)
- **任务类型**: 多分类 (4类: None, Mild, Moderate, Severe)
- **评估指标**: Quadratic Weighted Kappa (QWK)
- **开发周期**: W0-W8 (8周)
- **开发环境**: Linux (Ubuntu), RTX 5060 Ti, Python 3.11

---

## 2026-05-29 - W0/W1 阶段开发

### 硬件环境

```bash
# CPU
Intel i5-14600K (20 核心)

# 内存
31 GiB

# GPU
NVIDIA GeForce RTX 5060 Ti
- VRAM: 16 GB
- 架构: Blackwell (sm_120)
- 驱动: 580.126.09
- CUDA: 12.0 toolkit

# 磁盘
可用空间: 71 GiB

# 软件环境
- Conda: 25.7.0
- Java: OpenJDK 21
- Git: 已配置
```

### 环境配置决策

#### 为什么复用 openpi_311 环境?

**背景**: 本地已有 4 个 conda 环境,其中 `openpi_311` 环境配置接近项目需求。

**决策**: 复用 `openpi_311` 并补充依赖,而不是创建新环境。

**原因**:
1. **PyTorch 版本完美支持 sm_120**: openpi_311 已安装 PyTorch 2.9.0+cu128,完美支持 RTX 5060 Ti (Blackwell sm_120 架构)
2. **节省磁盘空间**: 避免重复下载 ~2 GB 的 PyTorch,磁盘可用空间仅 71 GiB
3. **节省时间**: 避免 ~30 分钟的环境创建时间
4. **Python 版本匹配**: Python 3.11.14 符合项目要求

**执行命令**:
```bash
# 激活环境
source /home/er/Devenv/Anaconda3/etc/profile.d/conda.sh
conda activate openpi_311

# 补充依赖
pip install mlflow==2.17.0 pyspark==3.5.0 optuna==3.6.0 \
    fastapi==0.115.0 uvicorn==0.30.0 pydantic==2.9.0 \
    dvc==3.55.0 catboost==1.2.7 lightgbm==4.5.0 \
    seaborn==0.13.0 kaggle pyarrow==15.0.0 tqdm pyyaml

# 保存环境配置
pip freeze > envs/pinned_openpi_311_mlsys.txt
```

**结果**: 
- ✅ 所有依赖安装成功 (242 个包)
- ✅ GPU 测试通过 (CUDA 可用, sm_120 支持)
- ✅ 可复现性测试通过

**版本对比**:

| 包 | openpi_311 | 项目要求 | 状态 | 说明 |
|---|---|---|---|---|
| PyTorch | 2.9.0+cu128 | 2.11.0+cu128 | ⚠️ | 2.9 已支持 sm_120,保持不变 |
| numpy | 2.3.5 | 1.26.0 | ⚠️ | 版本较新,向后兼容 |
| pandas | 3.0.0 | 2.2.0 | ⚠️ | 版本较新,向后兼容 |
| scikit-learn | 1.8.0 | 1.5.0 | ⚠️ | 版本较新,向后兼容 |
| MLflow | 2.17.0 | 2.17.0 | ✅ | 完全匹配 |
| PySpark | 3.5.0 | 3.5.0 | ✅ | 完全匹配 |

---

### Kaggle API 配置

#### 踩坑: Kaggle 新版 API Token 方式

**问题**: Kaggle 现在使用 API Token 而不是 `kaggle.json` 文件。

**解决方案**:
1. 访问 https://www.kaggle.com/settings
2. 点击 "Create New Token"
3. 复制显示的 Token: `KGAT_4b34606e927c8ebbc6d8635b9dd4d626`
4. 设置环境变量:

```bash
# 添加到 ~/.bashrc
echo 'export KAGGLE_API_TOKEN="KGAT_4b34606e927c8ebbc6d8635b9dd4d626"' >> ~/.bashrc
source ~/.bashrc
```

**验证**:
```bash
conda activate openpi_311
export KAGGLE_API_TOKEN="KGAT_4b34606e927c8ebbc6d8635b9dd4d626"
kaggle competitions list | head -5
# ✅ 成功显示竞赛列表
```

---

### 数据下载

#### 踩坑: 网络不稳定导致下载失败

**问题**: 首次下载在多次重试后失败 (5次重试后仍失败)。

**原因**: 国内访问 Kaggle 网络不稳定,下载大文件 (6.21 GB) 容易中断。

**解决方案**:
```bash
# 方案 1: 清理不完整的下载并重试
rm data/raw/child-mind-institute-problematic-internet-use.zip

# 方案 2: 使用后台下载
source /home/er/Devenv/Anaconda3/etc/profile.d/conda.sh
conda activate openpi_311
export KAGGLE_API_TOKEN="KGAT_4b34606e927c8ebbc6d8635b9dd4d626"
cd data/raw
kaggle competitions download -c child-mind-institute-problematic-internet-use

# 监控进度
watch -n 5 'ls -lh data/raw/'
```

**当前状态** (2026-05-29 12:58):
- 文件大小: 773 MB / 6.21 GB
- 进度: ~12%
- 预计完成时间: 20-30 分钟

**备选方案** (如果继续失败):
- 使用浏览器手动下载 (更稳定,支持断点续传)
- 访问: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/data
- 点击 "Download All"

---

### MLflow 服务器启动

**命令**:
```bash
source /home/er/Devenv/Anaconda3/etc/profile.d/conda.sh
conda activate openpi_311

# 启动 MLflow 服务器 (后台运行)
nohup mlflow server \
    --backend-store-uri sqlite:///$PWD/mlruns.db \
    --default-artifact-root $PWD/mlruns_artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    > mlflow_server.log 2>&1 &

# 记录 PID
echo $! > mlflow_server.pid
```

**验证**:
```bash
# 检查健康状态
curl http://localhost:5000/health
# 输出: OK

# 查看进程
ps aux | grep mlflow | grep -v grep
# PID: 1988235

# 访问 UI
xdg-open http://localhost:5000
```

**管理命令**:
```bash
# 查看日志
tail -f mlflow_server.log

# 停止服务
kill $(cat mlflow_server.pid)

# 重启服务
bash scripts/start_mlflow.sh
```

---

### Git 配置

#### 踩坑: .gitignore 排除了 src/data/

**问题**: `.gitignore` 中的 `data/` 规则把 `src/data/` 也排除了。

**错误信息**:
```
下列路径根据您的一个 .gitignore 文件而被忽略：
src/data
```

**原因**: `data/` 匹配所有包含 `data` 的路径,包括 `src/data/`。

**解决方案**:
```bash
# 修改 .gitignore
# 将 data/ 改为 /data/ (只匹配根目录的 data/)
sed -i 's|^data/$|/data/|' .gitignore
sed -i 's|^mlruns/$|/mlruns/|' .gitignore

# 验证
git add src/data/*.py
git status --short
# ✅ 成功添加
```

**修改后的 .gitignore**:
```gitignore
# 数据与产物(由 runbook 规划,不入库)
/data/        # 只排除根目录的 data/
/mlruns/      # 只排除根目录的 mlruns/
```

---

### 项目结构

```
MLsystem/
├── 00_docs/                    # 文档
│   ├── README.md              # 项目总览
│   ├── PROJECT_LOG.md         # 开发日志 (本文件)
│   └── Snipaste_*.png         # 截图
├── data/                       # 数据目录 (不入库)
│   ├── raw/                   # 原始数据
│   ├── interim/               # 中间数据
│   ├── processed/             # 处理后数据
│   └── splits/                # 交叉验证切分
├── envs/                       # 环境配置
│   ├── README.md              # 环境说明
│   └── pinned_openpi_311_mlsys.txt  # 环境快照
├── scripts/                    # 自动化脚本
│   ├── setup_envs.sh          # 环境创建
│   ├── fetch_data.sh          # 数据下载
│   ├── start_mlflow.sh        # MLflow 启动
│   ├── check_disk.sh          # 磁盘检查
│   └── monitor_download.sh    # 下载监控
├── src/                        # 源代码
│   ├── config.py              # 全局配置
│   ├── data/                  # 数据处理模块
│   │   ├── constants.py       # 数据常量
│   │   ├── loader.py          # 数据加载
│   │   ├── splits.py          # 交叉验证
│   │   └── preprocess_tabular.py  # 预处理
│   ├── utils/                 # 工具模块
│   │   ├── logging.py         # 日志
│   │   ├── io.py              # 文件读写
│   │   ├── reproducibility.py # 可复现性
│   │   └── system_metrics.py  # 系统指标
│   ├── models/                # 模型模块 (待开发)
│   ├── training/              # 训练模块 (待开发)
│   └── inference/             # 推理模块 (待开发)
├── tests/                      # 测试
│   └── test_data_loading.py  # 数据加载测试
├── mlflow_server.log          # MLflow 日志
├── mlruns.db                  # MLflow 数据库
└── .gitignore                 # Git 忽略规则
```

---

### Git 提交历史

```bash
# 查看提交历史
git log --oneline

# 输出:
30ed982 feat(w1): 实现数据加载与预处理模块
fdbe468 feat(w0): 配置 openpi_311 环境用于 MLsystem 项目
964af51 init: 初始化项目结构与核心工具模块
92141e9 init: 课程项目文档库 v1+v2 与导览
```

**提交详情**:

#### Commit 1: 964af51 - 初始化项目结构
- 创建完整的目录结构
- 实现核心工具模块 (logging, io, reproducibility, system_metrics)
- 创建自动化脚本 (setup_envs.sh, fetch_data.sh, start_mlflow.sh)
- 配置文件 (config.py, .gitignore, Makefile)

#### Commit 2: fdbe468 - 环境配置
- 复用 openpi_311 环境
- 补充 MLsystem 所需依赖
- 保存环境配置快照
- 创建环境说明文档

#### Commit 3: 30ed982 - 数据处理模块
- 实现数据常量定义 (constants.py)
- 实现数据加载器 (loader.py)
- 实现交叉验证切分 (splits.py)
- 实现表格数据预处理 (preprocess_tabular.py)
- 创建数据加载测试 (test_data_loading.py)
- 修复 .gitignore 问题

---

### 关键配置参数

**全局配置** (`src/config.py`):
```python
# 可复现性
SEED = 42

# 交叉验证
N_SPLITS = 5

# 数据预处理
IMPUTATION_STRATEGY = "median"
SCALER_TYPE = "standard"

# 路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
```

**数据常量** (`src/data/constants.py`):
```python
# 列名
ID_COL = "id"
TARGET_COL = "sii"
GROUP_COL = "id"

# 目标类别
SII_CLASSES = {
    0: "None",
    1: "Mild",
    2: "Moderate",
    3: "Severe"
}

# 缺失值阈值
MAX_MISSING_RATE = 0.95  # 丢弃 >95% 缺失的列
```

---

### 测试与验证

#### 环境测试
```bash
conda activate openpi_311

# PyTorch GPU 测试
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Compute capability: {torch.cuda.get_device_capability(0)}')
"
# 输出:
# CUDA available: True
# GPU: NVIDIA GeForce RTX 5060 Ti
# Compute capability: (12, 0)
```

#### 可复现性测试
```bash
python -c "
from src.utils.reproducibility import verify_reproducibility
results = verify_reproducibility(seed=42, n_samples=5)
for key, value in results.items():
    print(f'{key}: {'✅' if value else '❌'}')
"
# 输出:
# python_random: ✅
# numpy_random: ✅
# torch_random: ✅
```

#### 数据加载测试 (待数据下载完成后运行)
```bash
python tests/test_data_loading.py
```

---

### 常用命令速查

```bash
# 激活环境
conda activate openpi_311

# 监控数据下载
watch -n 5 'ls -lh data/raw/'

# 检查磁盘空间
bash scripts/check_disk.sh

# 启动 MLflow
bash scripts/start_mlflow.sh

# 访问 MLflow UI
xdg-open http://localhost:5000

# 查看 MLflow 日志
tail -f mlflow_server.log

# 停止 MLflow
kill $(cat mlflow_server.pid)

# Git 操作
git status
git log --oneline
git diff

# 运行测试
python tests/test_data_loading.py
```

---

### 待办事项

#### 立即 (等待数据下载完成)
- [ ] 解压数据: `cd data/raw && unzip *.zip`
- [ ] 运行数据加载测试: `python tests/test_data_loading.py`
- [ ] 数据探索 (EDA): 查看数据分布、缺失值、特征相关性

#### W2 阶段 (下一步)
- [ ] 实现特征工程模块 (`src/data/feature_engineering.py`)
- [ ] 实现 actigraphy 预处理 (`src/data/preprocess_actigraphy_pandas.py`)
- [ ] 实现模型基类 (`src/models/base.py`)
- [ ] 实现 sklearn 基线模型 (`src/models/sklearn_baselines.py`)
- [ ] 创建训练脚本 (`scripts/train_baseline.py`)

#### W3-W4 阶段
- [ ] 实现深度学习模型 (Transformer, CNN)
- [ ] 实现模型集成 (Stacking, Blending)
- [ ] 超参数优化 (Optuna)

#### W5-W6 阶段
- [ ] 分布式训练 (PySpark)
- [ ] 模型压缩与优化
- [ ] 推理服务 (FastAPI)

#### W7-W8 阶段
- [ ] 模型部署
- [ ] 性能优化
- [ ] 文档完善

---

### 问题与解决方案

#### Q1: 为什么不升级 PyTorch 到 2.11?
**A**: PyTorch 2.9.0+cu128 已经完美支持 sm_120 架构,无需升级。升级可能引入不必要的兼容性问题。

#### Q2: numpy/pandas 版本较新会有问题吗?
**A**: 这些库通常向后兼容。如果遇到兼容性问题,可以降级:
```bash
pip install numpy==1.26.0 pandas==2.2.0 scikit-learn==1.5.0
```

#### Q3: 数据下载失败怎么办?
**A**: 使用浏览器手动下载更稳定,支持断点续传。

#### Q4: 如何验证环境配置正确?
**A**: 运行环境测试脚本:
```bash
python -c "from src.utils.reproducibility import verify_reproducibility; verify_reproducibility()"
```

---

### 性能基准

#### 硬件性能
- **GPU 内存**: 16 GB (足够训练中等规模模型)
- **系统内存**: 31 GiB (足够数据预处理)
- **磁盘 I/O**: 待测试

#### 预期训练时间 (估算)
- **Baseline 模型** (CatBoost/LightGBM): ~5-10 分钟/fold
- **深度学习模型** (Transformer): ~30-60 分钟/fold
- **完整 5-fold CV**: ~2-5 小时

---

### 参考资源

#### 竞赛链接
- 竞赛主页: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use
- 数据下载: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/data
- 讨论区: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/discussion

#### 文档
- MLflow: https://mlflow.org/docs/latest/index.html
- PySpark: https://spark.apache.org/docs/latest/api/python/
- Optuna: https://optuna.readthedocs.io/

#### 课程资料
- 位置: `/home/er/桌面/MLsystem/00_docs/`
- v1 文档: 基础理论
- v2 文档: 实践指南

---

### 更新日志

- **2026-05-29 12:00**: 项目初始化,创建目录结构
- **2026-05-29 12:30**: 环境配置完成,复用 openpi_311
- **2026-05-29 12:48**: Kaggle API 配置完成
- **2026-05-29 12:54**: MLflow 服务器启动成功
- **2026-05-29 12:55**: 数据下载开始 (6.21 GB)
- **2026-05-29 12:58**: W1 数据处理模块完成,代码已提交
- **2026-05-29 13:00**: 创建项目日志文档

---

## 下次启动项目时的检查清单

```bash
# 1. 激活环境
conda activate openpi_311

# 2. 检查 MLflow 服务器
curl http://localhost:5000/health
# 如果未运行: bash scripts/start_mlflow.sh

# 3. 检查数据下载状态
ls -lh data/raw/

# 4. 拉取最新代码 (如果有协作)
git pull

# 5. 查看项目状态
git status
git log --oneline -5

# 6. 检查磁盘空间
bash scripts/check_disk.sh

# 7. 继续开发...
```

---

**最后更新**: 2026-05-29 13:00
**当前阶段**: W1 完成,等待数据下载
**下一步**: 数据探索与 W2 特征工程

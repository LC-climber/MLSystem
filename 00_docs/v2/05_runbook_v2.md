# 环境与数据落地手册 v2

- 文档编号: `MLSYS-2026S-CC-RUNBOOK-v2`
- 日期: `2026-04-18`
- 作用: 让任何新组员拿到本目录后,能在 **一天之内** 把环境 + 数据 + MLflow server 全部跑起来
- 对应 v1: v1 系列**没有**对应文件,本文档为新增
- 与其他 cc/ 文件的关系:
  - `02_charter_v2.md` §2.2 给出环境矩阵抽象,本文档给具体命令
  - `03_plan_p1_v2.md` / `04_plan_p2_v2.md` 假定环境已就绪,本文档是前置依赖

> **⚠️ 实际落地变更(2026-05-29):环境部分未按本手册执行。**
> §0 step 1 与 §2 设计的"三套 conda 环境(`mlsys_cpu` / `mlsys_gpu_local` / `mlsys_gpu_remote`)+ `scripts/setup_envs.sh`"为 2026-04 规划方案,**实际未采用**。
> 落地改为**复用现有 `openpi_311` 单环境**(已含 PyTorch 2.9.0+cu128,原生支持 sm_120),原因与依赖清单见 [`../../envs/README.md`](../../envs/README.md) 与 [`../PROJECT_LOG.md`](../PROJECT_LOG.md)。
> 本手册 §3 数据 / §4 MLflow / §5 磁盘预算 / §6 VRAM / §7 GPU fallback **仍然有效**;§2 保留作异机重建与多环境规划参考。

## 0. TL;DR: 开机四步走

```bash
# 1. 环境:实际复用 openpi_311(见上方"实际落地变更"),无需建三套环境
conda activate openpi_311      # 异机重建见 envs/README.md

# 2. 配置 Kaggle API + 下载数据(~1 h,取决于网速)
bash scripts/fetch_data.sh     # 脚本内容见 §3.3

# 3. 校验磁盘预算
bash scripts/check_disk.sh     # 如果 >55 GiB,自动切 WISDM

# 4. 启动 MLflow server
bash scripts/start_mlflow.sh   # http://localhost:5000
```

四步完成后: `openpi_311` 环境可用、`data/raw/` 有数据、MLflow UI 可访问。

## 1. 前置检查

### 1.1 操作系统

- **强烈推荐**: Linux 原生(Ubuntu 22.04 / 24.04)或 Windows 11 + WSL2 (Ubuntu 22.04 LTS)
- Windows 原生: 5060 Ti 的 sm_120 支持较差,不推荐;但可用于 CPU 端和远程 4090 SSH 开发
- macOS: 不在本项目支持范围

### 1.2 NVIDIA 驱动

本地 5060 Ti 需要 **R570+**,必须先确认:

```bash
nvidia-smi
# 必看输出: Driver Version: 570.xx.xx 或更高
#          CUDA Version: 12.8
```

若驱动低于 R570:
- Linux: `sudo apt install nvidia-driver-570` 或从 NVIDIA 官网下载 `.run` 安装包
- WSL2: 在 Windows 主机装最新 Game Ready Driver 或 Studio Driver,WSL2 内使用主机驱动

### 1.3 Conda / Mamba

```bash
conda --version   # 应为 25.x 或更高(charter 已验证 25.7.0)
```

建议安装 `mamba` 加速依赖求解:
```bash
conda install -n base -c conda-forge mamba
```

### 1.4 磁盘可用

```bash
df -h $HOME
# 要求: 至少 60 GiB 可用
```

本项目磁盘预算见 §5,硬上限 66 GiB。

### 1.5 Java(给 Spark 用)

```bash
java -version   # 需要 11 或 17
```

若缺: `sudo apt install openjdk-17-jre-headless`

## 2. 环境搭建(Conda × 3)

> ⚠️ **本节(三套环境 + `setup_envs.sh`)为规划方案,实际未采用**;落地复用 `openpi_311` 单环境,见本文件顶部说明与 [`../../envs/README.md`](../../envs/README.md)。下方内容保留作异机重建 / 多环境参考。

### 2.1 共用约定

- Python 版本: **3.11**(兼顾 PyTorch 2.11 stable 和 2.10 nightly)
- 随机种子: `seed=42`(在所有 config 里读同一个常量)
- 项目根目录假设为 `$PROJECT_ROOT`,建议 `~/code/mlsys-2026s-piu`

### 2.2 `mlsys_cpu` — 数据预处理 / Spark / sklearn

```bash
mamba create -n mlsys_cpu python=3.11 -y
mamba activate mlsys_cpu

mamba install -c conda-forge -y \
  numpy=1.26 pandas=2.2 pyarrow=15 \
  scikit-learn=1.5 scipy=1.13 \
  matplotlib=3.9 seaborn=0.13 \
  jupyterlab ipykernel \
  openjdk=17 \
  pyspark=3.5 \
  polars=0.20 \
  psutil tqdm pyyaml \
  kaggle

pip install mlflow==2.17.0 dvc==3.55.0 optuna==3.6.0 shap==0.45.0
```

验证:
```bash
python -c "import pyspark; print(pyspark.__version__)"   # 3.5.x
python -c "from pyspark.sql import SparkSession; s=SparkSession.builder.master('local[2]').appName('t').getOrCreate(); print(s.version); s.stop()"
```

### 2.3 `mlsys_gpu_local` — 本地 5060 Ti 调试

> ⚠️ 2026-04 最新情况: 若 PyTorch 2.11 stable 已完整支持 sm_120,走 stable 通道;否则走 nightly。**先跑 2.4.1 stable 测试,失败再退到 2.4.2 nightly。**

#### 2.4.1 首选 — stable 通道(测试用)

```bash
mamba create -n mlsys_gpu_local python=3.11 -y
mamba activate mlsys_gpu_local

pip install --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.11.0 torchvision==0.21.0 torchaudio==2.11.0

# sm_120 烟雾测试
python -c "
import torch
print('torch:', torch.__version__)
print('cuda avail:', torch.cuda.is_available())
print('cuda version:', torch.version.cuda)
print('device:', torch.cuda.get_device_name(0))
print('capability:', torch.cuda.get_device_capability(0))   # 应为 (12, 0)
x = torch.randn(4, 4, device='cuda')
y = x @ x.T
print('kernel ok:', y.shape)
"
```

若最后一步报 `no kernel image is available for execution on the device`,说明 stable 尚未 land sm_120,走 2.4.2。

#### 2.4.2 Fallback — nightly 通道(sm_120 兼容性更稳妥)

```bash
mamba create -n mlsys_gpu_local python=3.11 -y
mamba activate mlsys_gpu_local

pip install --pre --index-url https://download.pytorch.org/whl/nightly/cu128 \
  torch torchvision torchaudio
```

建议记录当时 `pip freeze | grep torch` 的版本到 `envs/pinned_gpu_local.txt`,锁定不再升级。

#### 通用追加包

```bash
pip install mlflow==2.17.0 optuna==3.6.0 fastapi==0.115.0 uvicorn==0.30.0 \
            pydantic==2.9.0 tqdm pyyaml pandas==2.2.3 scikit-learn==1.5.2 \
            catboost==1.2.7 lightgbm==4.5.0 pyarrow==15.0.0
```

### 2.4 `mlsys_gpu_remote` — 远程 4090 正式训练

```bash
mamba create -n mlsys_gpu_remote python=3.11 -y
mamba activate mlsys_gpu_remote

# 远程 4090 (sm_89) 完全兼容 stable,无需 nightly
pip install --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.11.0 torchvision==0.21.0 torchaudio==2.11.0

pip install mlflow==2.17.0 optuna==3.6.0 fastapi==0.115.0 uvicorn==0.30.0 \
            pydantic==2.9.0 tqdm pyyaml pandas==2.2.3 scikit-learn==1.5.2 \
            catboost==1.2.7 lightgbm==4.5.0 pyarrow==15.0.0
```

### 2.5 封装脚本 `scripts/setup_envs.sh`(按需创建)

此脚本把 §2.2-2.4 的命令串起来,供新组员一键执行。建议在组员加入时初始化后提交到 git。

### 2.6 固定版本文件

每个环境就位后生成 `pinned`:

```bash
conda activate mlsys_cpu && pip freeze > envs/pinned_cpu.txt
conda activate mlsys_gpu_local && pip freeze > envs/pinned_gpu_local.txt
conda activate mlsys_gpu_remote && pip freeze > envs/pinned_gpu_remote.txt
```

提交 git,以后重现按 pinned 安装即可。

## 3. 数据获取

### 3.1 Kaggle API 配置

#### 一次性:

1. 登录 Kaggle → Account → Create New API Token
2. 下载 `kaggle.json`,放到 `~/.kaggle/kaggle.json`
3. 权限: `chmod 600 ~/.kaggle/kaggle.json`
4. 在 `mlsys_cpu` 环境已装 `kaggle` 包

#### 首次运行前同意竞赛规则:

打开浏览器访问 `https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/rules` → 点 **I Understand and Accept**。不接受规则 API 会报 `403 Forbidden`。

### 3.2 下载 PIU 主数据

```bash
mkdir -p data/raw
cd data/raw
kaggle competitions download -c child-mind-institute-problematic-internet-use
unzip child-mind-institute-problematic-internet-use.zip
rm child-mind-institute-problematic-internet-use.zip   # 省 6 GiB
ls
# 期望看到: train.csv, test.csv, sample_submission.csv, series_train.parquet/, series_test.parquet/ 等
cd ../..
```

### 3.3 下载镜像 fallback

若 Kaggle 官方 CDN 不可用,使用社区镜像:

```bash
# 镜像 A(tabular 主部分)
kaggle datasets download -d akirahoimancheng/child-mind-institute-problematic-internet-use -p data/raw/mirror/ --unzip
```

注意: 镜像可能滞后于官方修正,以官方为准。

### 3.4 WISDM 备用数据(硬兜底)

若触发 WISDM 切换:

```bash
mkdir -p data/raw_wisdm && cd data/raw_wisdm
wget https://www.cis.fordham.edu/wisdm/includes/datasets/latest/WISDM_ar_latest.tar.gz
tar -xzf WISDM_ar_latest.tar.gz
rm WISDM_ar_latest.tar.gz
```

### 3.5 数据完整性校验

```bash
cd data/raw
md5sum train.csv test.csv > ../data_checksums.md5
# 后续新机器: md5sum -c data_checksums.md5
```

### 3.6 DVC 初始化(P2 准备)

```bash
cd $PROJECT_ROOT
dvc init
dvc add data/raw
git add data/raw.dvc .gitignore .dvc/config
git commit -m "dvc: track raw PIU data"
# 可选: dvc remote add -d s3-remote s3://...  # 课程阶段用本地存储即可
```

## 4. MLflow server

### 4.1 本地启动(开发用)

```bash
conda activate mlsys_cpu
mkdir -p mlruns_artifacts
mlflow server \
  --backend-store-uri sqlite:///$PWD/mlruns.db \
  --default-artifact-root $PWD/mlruns_artifacts \
  --host 0.0.0.0 \
  --port 5000
```

访问: http://localhost:5000

### 4.2 远程访问(组员共享)

如果想让组员远程看 MLflow:

```bash
# SSH tunnel
ssh -L 5000:localhost:5000 user@host_with_mlflow
# 浏览器打开 http://localhost:5000
```

### 4.3 训练脚本里记录

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("mlsys_p1_piu_systemwise")

with mlflow.start_run(run_name="20260501_B_mlp_v1"):
    mlflow.log_params({"model": "mlp", "feat_version": "v1", "seed": 42})
    # ... 训练 ...
    mlflow.log_metrics({"val_qwk": 0.41, "val_macro_f1": 0.39})
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.pytorch.log_model(model, "model")
```

## 5. 磁盘预算(66 GiB 硬上限)

| 项 | 估算 | 触达时机 | 备注 |
|---|---|---|---|
| PIU 原始(解压后) | ~12 GiB | W0 | 删 zip 节省 6 GiB |
| actigraphy parquet 缓存 | ~5 GiB | W1 | 列存 + snappy |
| feat_v1/v2/v3 | ~0.1 GiB | W1-W2 | 小 |
| MLflow artifacts | ~5 GiB | W5-W8 | 含混淆矩阵/权重 |
| 模型 checkpoint + Registry | ~2 GiB | W5-W8 | |
| Spark temp(shuffle) | ~10 GiB | W2 | 需 `spark.local.dir` 指向 `~/spark_tmp` |
| Docker 镜像 | ~3 GiB | W7 | `docker system prune -a` 可回收 |
| Conda envs × 3 | ~15 GiB | W0 | 主要 torch wheel 占大头 |
| git + 代码 | ~0.5 GiB | 常驻 | |
| **合计** | **~52.6 GiB** | | 留 13 GiB 冗余 |

### 5.1 磁盘监控脚本

```bash
# scripts/check_disk.sh
#!/bin/bash
USED=$(df -BG ~ | tail -1 | awk '{print $3}' | sed 's/G//')
AVAIL=$(df -BG ~ | tail -1 | awk '{print $4}' | sed 's/G//')
echo "HOME used: ${USED}G, avail: ${AVAIL}G"
if [ "$AVAIL" -lt 10 ]; then
  echo "⚠️  剩余空间 < 10 GiB,触发 WISDM 降级评估"
  echo "    参见 06_risk_and_eval_v2.md §6 切换 SOP"
  exit 1
fi
```

建议 W1 末、W3 末、W5 末、W7 末各跑一次。

### 5.2 Spark shuffle 目录指定

在 SparkSession 初始化时:

```python
spark = (SparkSession.builder
    .master("local[20]")
    .appName("piu_featuring")
    .config("spark.local.dir", f"{os.path.expanduser('~')}/spark_tmp")
    .config("spark.driver.memory", "20g")
    .config("spark.executor.memory", "20g")
    .getOrCreate())
```

注意 `spark.local.dir` 不要指向小分区。

## 6. VRAM × 模型 × batch 映射

### 6.1 5060 Ti 16GB(本地 nightly)

| 模型 | 参数 | 推荐 batch(训练) | 备注 |
|---|---|---|---|
| tabular MLP (128-64) | <0.1M | 2048 | 调试 |
| 1D CNN actigraphy (win=30s) | ~2M | 512 | 半精度可到 1024 |
| late-fusion 双分支 | ~5M | 256 | mixed precision on |
| light Transformer (4L) | ~10M | 128 | 建议在 4090 上 |

### 6.2 4090 24GB(远程)

| 模型 | 推荐 batch(训练) | Optuna trial 时长估算 |
|---|---|---|
| tabular MLP | 8192 | ~2 min |
| 1D CNN | 2048 | ~8 min |
| late-fusion | 1024 | ~12 min |
| light Transformer | 512 | ~20 min |

100 trials × Optuna 大致: MLP ~3h30m / 1D CNN ~13h / late-fusion ~20h。融合模型 trials 请压到 50 以下。

### 6.3 OOM 应急

- 减半 batch
- `torch.cuda.empty_cache()`
- `torch.backends.cudnn.benchmark = True`(若输入尺寸固定)
- 使用 mixed precision: `torch.autocast(device_type='cuda', dtype=torch.bfloat16)`

## 7. 三级 GPU Fallback

当远程 4090 不可用:

### Tier 1 — 远程 4090(默认)

- 连接: `ssh user@gpu-server`
- 同步代码: `rsync -avz $PROJECT_ROOT/ user@gpu-server:~/project/`
- MLflow: SSH tunnel 到本地 5000 端口

### Tier 2 — Kaggle Notebook(免费)

- 每周免费 T4×2 30 小时
- 数据直接绑定 PIU 竞赛 dataset,免下载
- 限制: 单次 session 9 小时,无持久 MLflow server
- 用法: notebook 里用 `mlflow` 写到 tracking server(通过 ngrok 暴露本地 5000)或直接 `log_to_file` 事后补录
- 适合: 单次长训练、Optuna trials 的 remote run

### Tier 3 — AutoDL / Colab Pro(按需)

- AutoDL: ¥3-6/小时(4090 单卡),按需开机
- Colab Pro: $9.99/月,A100 有概率,T4 稳定
- 用法: SSH 到 AutoDL 实例后按 Tier 1 流程

## 8. 项目目录结构(推荐)

```
mlsys-2026s-piu/
├── 00_docs/
│   ├── cc/                          ← 本文档所在
│   ├── memos/
│   ├── plans/
│   ├── templates/
│   └── reports/
├── envs/
│   ├── pinned_cpu.txt
│   ├── pinned_gpu_local.txt
│   └── pinned_gpu_remote.txt
├── data/
│   ├── raw/                         ← Kaggle 下载 (12 GiB, 入 DVC)
│   ├── interim/                     ← 清洗中间产物
│   ├── processed/                   ← feat_v1/v2/v3.parquet
│   ├── splits/                      ← stratified_group_kfold_seed42.csv
│   └── raw_wisdm/                   ← 兜底
├── src/
│   ├── config/                      ← hydra/YAML 配置
│   ├── data/                        ← preprocess_*.py
│   ├── features/                    ← feat_v*.py
│   ├── models/
│   │   ├── sklearn_baselines.py
│   │   ├── spark_baselines.py
│   │   └── torch_baselines.py
│   ├── experiments/
│   │   ├── run_p1_systemwise.py
│   │   ├── run_p2_optuna.py
│   │   └── run_p2_fusion.py
│   ├── serving/
│   │   ├── app.py                   ← FastAPI
│   │   └── schemas.py
│   └── utils/
├── scripts/
│   ├── setup_envs.sh
│   ├── fetch_data.sh
│   ├── check_disk.sh
│   ├── start_mlflow.sh
│   └── release_modelscope.sh
├── docker/
│   ├── Dockerfile.infer
│   └── Dockerfile.train
├── notebooks/
│   ├── p1_eda.ipynb
│   └── p1_ablation.ipynb
├── reports/
│   ├── p1/
│   └── p2/
├── Makefile
├── .dvc/
├── .gitignore
├── environment.yml                  ← 三套环境汇总(说明用,非实际安装)
└── README.md
```

## 9. Makefile 示范

```makefile
.PHONY: data features train eval register release serve help

SEED := 42

help:
	@echo "make data       — 从 Kaggle 拉取 PIU 原始数据"
	@echo "make features   — 构建 feat_v1 / v2 / v3"
	@echo "make train      — 跑 P1 systemwise 实验 + P2 baseline"
	@echo "make eval       — 评估 champion 模型"
	@echo "make register   — 在 MLflow 注册 champion"
	@echo "make release    — 发布到 ModelScope + HF Hub"
	@echo "make serve      — 本地启动 FastAPI"

data:
	bash scripts/fetch_data.sh

features:
	conda run -n mlsys_cpu python src/features/build_feat_v1.py --seed $(SEED)
	conda run -n mlsys_cpu python src/features/build_feat_v2_pandas.py --seed $(SEED)
	conda run -n mlsys_cpu python src/features/build_feat_v2_spark.py --seed $(SEED)
	conda run -n mlsys_cpu python src/features/build_feat_v3_fusion.py --seed $(SEED)

train:
	conda run -n mlsys_cpu python src/experiments/run_p1_systemwise.py --seed $(SEED)
	conda run -n mlsys_gpu_local python src/experiments/run_p2_baseline.py --seed $(SEED)

eval:
	conda run -n mlsys_gpu_local python src/experiments/eval_champion.py --seed $(SEED)

register:
	conda run -n mlsys_cpu python src/experiments/register_champion.py

release:
	bash scripts/release_modelscope.sh
	bash scripts/release_huggingface.sh

serve:
	conda run -n mlsys_gpu_local uvicorn src.serving.app:app --host 0.0.0.0 --port 8000
```

## 10. 常见故障排查

### 10.1 `CUDA error: no kernel image is available for execution on the device`

- 本地 5060 Ti: 换 nightly,见 §2.4.2
- 远程 4090: 确认 CUDA 12.8,`nvidia-smi` 看驱动 >=535,torch 版本正确

### 10.2 Kaggle 下载 403

- 未接受竞赛规则
- `kaggle.json` 权限错误
- API key 过期,重新生成

### 10.3 Spark `OutOfMemoryError`

- 增 `spark.driver.memory` 和 `spark.executor.memory`
- 减 batch / 分区数
- 检查 `spark.local.dir` 是否指向大分区

### 10.4 MLflow artifact 无法上传

- 确认 `--default-artifact-root` 路径存在且可写
- 检查 server 版本与 client 版本差不超过 1 major(都用 2.17.x)

### 10.5 Docker 构建 OOM

- 扩大 Docker Desktop 内存配额到 8 GiB+
- 用多阶段构建减少中间层

## 11. 参考

- Kaggle API: https://github.com/Kaggle/kaggle-api
- PyTorch 安装: https://pytorch.org/get-started/locally/
- PyTorch sm_120 追踪: https://github.com/pytorch/pytorch/issues/164342
- Spark 配置: https://spark.apache.org/docs/latest/configuration.html
- MLflow 部署: https://mlflow.org/docs/latest/tracking/server.html
- DVC 快速开始: https://dvc.org/doc/start
- Docker 多阶段: https://docs.docker.com/build/building/multi-stage/

## 12. 修订记录

- `v2 | 2026-04-18`: 首版。v1 系列无对应文件,本文档为新增,提供完整落地命令、磁盘预算、VRAM 映射、三级 GPU fallback、项目结构、Makefile。

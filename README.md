# MLsystem — 机器学习系统课程项目(2026 春)

中国科学院大学《机器学习系统》课程的两项作业实现:

- **项目 1**: 多系统问题性互联网使用风险识别算法对比(单机 / 分布式 / 深度学习)
- **项目 2**: 基于 MLflow 的 PIU 风险识别 MLOps 实践与双渠道发布

主线数据为 Kaggle [Child Mind Institute — Problematic Internet Use](https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use),WISDM HAR 作为硬兜底。

## 快速开始

### 1. 环境搭建 (W0)

> 本项目**复用现有的 `openpi_311` conda 环境**(已含 PyTorch 2.9.0+cu128,完整支持 RTX 5060 Ti 的 sm_120),**不再单独创建环境**。决策依据与完整依赖清单见 [`envs/README.md`](envs/README.md)。

```bash
# 检查磁盘空间
bash scripts/check_disk.sh

# 激活环境(已配置好,无需新建;异机重建见 envs/README.md)
conda activate openpi_311

# 配置 Kaggle API
# 1. 访问 https://www.kaggle.com/settings
# 2. 创建 API Token,下载 kaggle.json
# 3. 放置到 ~/.kaggle/kaggle.json
# 4. 设置权限: chmod 600 ~/.kaggle/kaggle.json

# 下载数据 (~1 小时)
bash scripts/fetch_data.sh

# 启动 MLflow 服务器 (后台运行)
bash scripts/start_mlflow.sh &
```

### 2. 开发流程

```bash
# 激活环境(单一环境,覆盖数据处理 / Spark / sklearn / PyTorch)
conda activate openpi_311
# 若已配置 direnv,cd 进项目目录会自动激活(见 .envrc)

# 使用 Makefile
make help           # 查看所有命令
make check-disk     # 检查磁盘空间
make features       # 生成特征
make train-p1       # 运行项目 1
make train-p2       # 运行项目 2
make test           # 运行测试
```

### 3. 项目结构

```
.
├── 00_docs/            # 项目文档 (v1 归档, v2 当前版本)
├── data/               # 数据目录
│   ├── raw/            # 原始数据 (DVC 跟踪)
│   ├── interim/        # 中间处理结果
│   ├── processed/      # 特征工程输出
│   └── splits/         # 交叉验证切分
├── src/                # 源代码
│   ├── config.py       # 全局配置
│   ├── data/           # 数据加载与预处理
│   ├── models/         # 模型实现 (sklearn/Spark/PyTorch)
│   ├── training/       # 训练循环
│   ├── evaluation/     # 评估与可视化
│   ├── mlflow_utils/   # MLflow 集成
│   ├── deployment/     # FastAPI 推理服务 (P2)
│   ├── utils/          # 工具函数
│   ├── experiments/    # 实验脚本
│   └── scripts/        # CLI 入口
├── scripts/            # Shell 脚本
├── tests/              # 单元测试
├── envs/               # Conda 环境锁定文件
├── Makefile            # 任务编排
└── README.md           # 本文件
```

## 硬件要求

- **CPU**: Intel i5-14600K (20 核)
- **RAM**: 31 GiB
- **GPU**: RTX 5060 Ti (16 GB VRAM, sm_120)
- **磁盘**: 66 GiB 可用空间 (硬上限)
- **OS**: Linux (推荐) 或 WSL2

## 环境说明

**单一环境 `openpi_311`(复用)**,覆盖单机 / 分布式 / 深度学习 / 部署全流程:

- Python 3.11.14 + PyTorch 2.9.0+cu128(支持 RTX 5060 Ti sm_120)+ CUDA 12.8
- sklearn 1.8 / PySpark 3.5 / MLflow 2.17 / CatBoost / LightGBM / Optuna / FastAPI

> 早期规划的 `mlsys_cpu / mlsys_gpu_local / mlsys_gpu_remote` 三套环境矩阵(见 `00_docs/v2/02_charter_v2.md` §2.2、`05_runbook_v2.md` §2)**未采用**;复用 openpi_311 的原因见 [`envs/README.md`](envs/README.md)。

## 关键配置

- **随机种子**: 42 (全局)
- **交叉验证**: 5-fold StratifiedGroupKFold
- **主指标**: P1=Macro-F1, P2=QWK
- **MLflow**: http://localhost:5000

## 文档导览

- 项目总览: `00_docs/v2/01_overview_v2.md`
- 立项书: `00_docs/v2/02_charter_v2.md`
- P1 计划: `00_docs/v2/03_plan_p1_v2.md`
- P2 计划: `00_docs/v2/04_plan_p2_v2.md`
- 执行手册: `00_docs/v2/05_runbook_v2.md`
- 风险评估: `00_docs/v2/06_risk_and_eval_v2.md`

## 团队分工

| 角色 | 职责 |
|---|---|
| A | 数据获取与单机 / Spark 实验 |
| B | 深度学习与远程 GPU 训练 |
| C | MLOps、推理服务与双渠道发布 |

## 当前状态

**W2 阶段进行中** — 环境、数据 pipeline、切分协议、feat_v1 与三系统对比表 1 均已完成:

- ✅ W0 环境:复用 `openpi_311`(见 [`envs/README.md`](envs/README.md))
- ✅ W1 数据:加载 / 预处理 / 切分打通;已处理 `sii` 标签缺失与 PCIAT 标签泄漏
- ✅ W2 对比表 1:sklearn / Spark / PyTorch × LR/MLP × 5-fold 全跑通,入 MLflow 与 `reports/p1_systemwise_feat_v1.csv`
- 🚧 进行中:feat_v2 actigraphy 滑窗统计(pandas 版 + Spark 版对比)

详细进度见 [`00_docs/PROJECT_LOG.md`](00_docs/PROJECT_LOG.md)。

## License

本项目为课程作业,仅供学习使用。

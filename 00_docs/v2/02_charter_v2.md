# 机器学习系统课程项目立项与计划 v2

- 文档编号: `MLSYS-2026S-CHARTER-v2`
- 课程名称: `机器学习系统`
- 原版本: `00_docs/v1/mlsys_project_charter_v1.md`(2026-04-16)
- 修订日期: `2026-04-18`
- 修订人: `Claude Code 评审与优化`
- 当前状态: `v2 draft`,待课程组 review 后转 `v2 decided`
- 适用范围: `项目实践及演示汇报-1`、`项目实践及演示汇报-2`

## 0. 相对 v1 的改动点

| # | v1 写法 | v2 改为 | 原因 |
|---|---|---|---|
| 1 | 主线 HAR(WISDM/PAMAP2),备选 UrbanSound8K | **主线 PIU(Kaggle),硬兜底 WISDM** | 与 portfolio_v1 收敛;PIU 的 tabular+actigraphy 让 Spark 真正有意义,避免"伪分布式悖论" |
| 2 | 环境 `PyTorch 2.7.x + cu128` | `torch 2.11 stable + cu128`(远程 4090) / `torch 2.10+ nightly + cu128`(本地 5060 Ti) | 2026-04 stable 已到 2.11;sm_120 在 stable 仍未完整支持需 nightly |
| 3 | P1 指标 `Accuracy / Macro-F1 / Weighted-F1` | P1 主 **Macro-F1**,辅 QWK / Balanced Accuracy | Weighted-F1 被 majority class 主导不适合有序不平衡任务;QWK 是 PIU 官方指标 |
| 4 | P2 指标未统一写 | P2 主 **QWK**,辅 Macro-F1 / Log Loss | 对齐 Kaggle 官方;Log Loss 捕捉概率校准 |
| 5 | 分布式系统"本机伪分布式 / 单机多进程" | 明确 Spark 的主阵地从"模型训练"挪到 **actigraphy 时序预处理** | 3000 样本分类上 Spark 必输,预处理阶段有真实数据量(数 GB) |
| 6 | 进度只列"第一阶段 / 第二阶段..."5 段 | 细化为 10 周周历 W0-W9,含 W4 中期 / W9 最终两个硬锚点 | 颗粒度可度量 |
| 7 | 团队"3 人或 2 人"两种写法并列 | 锁 3 人,明确 A/B/C 三个角色的每周产出 | 责任可追溯 |
| 8 | 发布只 ModelScope | ModelScope 主 + HuggingFace Hub 镜像 | MLOps 深度加分,且互为 fallback |
| 9 | 磁盘只剩 66 GiB,无预算 | `05_runbook_v2.md` 给出 7 项占用预算,留 15 GiB 冗余 | 避免中途磁盘爆 |
| 10 | 部分引用链接定位不准(`scce.ucas.ac.cn`) | 统一使用 `onestop` 和 `aipt.ucas.ac.cn` | 引用准确 |

## 1. 本版结论

**主方案**: `MLSYS-2026S-P1/P2-PIU` — 基于 Kaggle `Child Mind Institute — Problematic Internet Use` 的多系统对比 + MLOps 发布

- 主题: 青少年问题性互联网使用(PIU)风险识别。数据集同时包含 `tabular 健康/问卷/体测特征` 和 `actigraphy 原始加速度时序`,是典型的"真实世界多模态 ML 任务"。
- 项目 1: `多系统 PIU 风险识别算法对比`(单机 / 分布式 / 深度学习系统)
- 项目 2: `基于 MLflow 的 PIU 风险识别 MLOps 实践与双渠道发布`

**硬兜底**: `MLSYS-2026S-P1/P2-WISDM` — 基于 UCI/Fordham `WISDM` HAR 数据的同主题降级版

- 触发条件: PIU 磁盘占用超预算 / Kaggle API 连续 3 天无法下载 / actigraphy 原始数据处理在本地 OOM 无法用 Spark 规避
- 切换成本: ~3 天(代码架构通用,需重写数据加载 adapter 和特征工程)

### 1.1 为什么 PIU 比 HAR 更适合本课程

- **Spark 的科学性**: PIU 的 actigraphy 数据每参与者有连续数周原始加速度样本,聚合后仍是 `数 GB ~ 数十 GB` 级;用 Spark 做滑窗/统计抽取比 pandas 有真实收益。反观 WISDM 虽然样本更多(~2.98M 行),但预处理逻辑简单,Spark 的优势反而不如 PIU 明显。
- **多模态叙事**: PIU = tabular + actigraphy,天然有"特征工程 vs 端到端"的对比话题,两项作业都有空间讲。WISDM 纯时序,叙事面更窄。
- **新颖度**: PIU 是 2024 新赛,目前课程项目"撞题率"低于 HAR。
- **指标明确**: PIU 官方指标 QWK,有序分类,清晰无歧义。

### 1.2 什么情况下切回 WISDM

见 `06_risk_and_eval_v2.md` 的"降级决策流程"。简单说: W1 结束时若 PIU 仍没跑通 baseline,或磁盘超 55 GiB,立即切 WISDM。

## 2. 硬件与环境约束

### 2.1 硬件确认

- 本地:
  - CPU `Intel Core i5-14600K` / 20 逻辑核
  - RAM `31 GiB`
  - 磁盘可用 `66 GiB`(硬上限)
  - GPU `RTX 5060 Ti`,假设 `16 GB VRAM`,Blackwell sm_120
  - 驱动要求 `R570+`
  - OS 强烈建议 `Linux` 或 `Windows + WSL2 Ubuntu 22.04/24.04`
- 远程:
  - 单卡 `RTX 4090` / `24 GB VRAM` / sm_89
  - 使用窗口未确定,按三级 GPU fallback 处理

### 2.2 环境矩阵(Conda,三套并列)

| 环境名 | 用途 | Python | 核心包 | GPU |
|---|---|---|---|---|
| `mlsys_cpu` | 数据预处理 / Spark / sklearn / pandas | 3.11 | pyspark 3.5.x, scikit-learn 1.5+, pandas 2.2+, pyarrow, polars | 不用 |
| `mlsys_gpu_local` | 本地 5060 Ti 调试 / 演示保底 | 3.11 | **torch 2.10+ nightly + cu128**(sm_120 在 stable 2.11 若已 land 可回切),mlflow 2.x | 5060 Ti + R570+ + CUDA 12.8 |
| `mlsys_gpu_remote` | 远程 4090 正式训练 | 3.11 | **torch 2.11 stable + cu128**,mlflow 2.x,optuna 3.x | 4090,CUDA 12.8 |

具体安装命令见 `05_runbook_v2.md`。

> **落地变更(2026-05-29)**:上述三套环境矩阵为 2026-04 规划方案,**实际未采用**。落地改为**复用单一 `openpi_311` 环境**(Python 3.11.14 + PyTorch 2.9.0+cu128,已支持 sm_120,无需 nightly/stable 分流),原因与依赖清单见 [`../../envs/README.md`](../../envs/README.md) 与 [`../PROJECT_LOG.md`](../PROJECT_LOG.md)。本表保留作设计依据与异机 / 多环境重建参考。

### 2.3 关键版本事实(2026-04-18)

- PyTorch stable **2.11.0** 已发布,PyPI 默认 wheel 为 `cu130`;`cu130` 不支持 sm_120。
- 5060 Ti 需 `cu128` 分支,通过 `pip install torch --index-url https://download.pytorch.org/whl/cu128` 安装。
- 截至 2025-10,stable 通道对 sm_120 支持**仍未完善**,已验证可用的是 `torch 2.10.0.dev+cu128 (nightly)`。在 2026-04 应重新 check `torch 2.11 stable + cu128` 是否已 land sm_120,若已 land 则优先 stable。
- 远程 4090 (sm_89) 可直接用 `torch 2.11 stable + cu128`,没有 nightly 不稳定风险。

## 3. 命名规范

### 3.1 项目编号

- 课程总前缀: `MLSYS-2026S`
- 项目 1 编号: `MLSYS-2026S-P1-COMPARE-PIU`(主)/ `MLSYS-2026S-P1-COMPARE-WISDM`(兜底)
- 项目 2 编号: `MLSYS-2026S-P2-MLOPS-PIU`(主)/ `MLSYS-2026S-P2-MLOPS-WISDM`(兜底)

### 3.2 文件命名

- 立项书(现行): `00_docs/v2/02_charter_v2.md`
- P1 计划书(现行): `00_docs/v2/03_plan_p1_v2.md`
- P2 计划书(现行): `00_docs/v2/04_plan_p2_v2.md`
- 落地手册: `00_docs/v2/05_runbook_v2.md`
- 风险/评价: `00_docs/v2/06_risk_and_eval_v2.md`
- 便函: `00_docs/v1/memos/memo_YYYYMMDD_topic_vN.md`
- 阶段报告: `00_docs/report_p1_vN.md` / `00_docs/report_p2_vN.md`
- 中期汇报: `00_docs/midterm_slides_outline_vN.md`
- 最终汇报: `00_docs/final_slides_outline_vN.md`

### 3.3 版本规则

- `v2 draft`: 本次优化的初稿
- `v2 decided`: 课程组 review 通过后的锁定版
- `v3`: 有首轮实验结果后的迭代
- `v4`: 中期之后到最终提交前的迭代

任何重要调整新增便函(`memo_YYYYMMDD_*_vN.md`),不覆盖旧结论。

### 3.4 实验与 artifact 命名

- 实验: `mlflow_run_{date}_{member}_{brief}` 如 `mlflow_run_20260501_B_mlp_v1`
- 模型权重: `{model_arch}__{feat_ver}__{seed}.pt`
- 特征矩阵: `feat_{v1|v2|v3}__{cpu|spark}__{seed}.parquet`
- Checkpoint: 统一 `./checkpoints/`,不入 git

## 4. 项目 1 方案摘要

完整内容见 `03_plan_p1_v2.md`,此处只写要点:

### 4.1 目标

在 `单机 sklearn / 分布式 Spark / 深度学习 PyTorch` 三类系统中,围绕同一 PIU 任务实现统一算法家族,对比以下维度:

- **模型指标**: 主 `Macro-F1`,辅 `QWK` / `Balanced Accuracy`
- **训练效率**: 总训练时间 / 单 epoch 时间 / 吞吐量
- **推理效率**: 单样本 / 单批推理延迟
- **资源开销**: CPU-GPU 利用、峰值 RSS、模型大小
- **特征处理效率**: 从原始 actigraphy 到特征矩阵的端到端时间(**本轮的 Spark 真价值所在**)

### 4.2 算法家族

- 算法 A: `Logistic Regression`
  - 单机: `sklearn.linear_model.LogisticRegression`
  - 分布式: `pyspark.ml.classification.LogisticRegression`
  - 深度学习: PyTorch 单层线性
- 算法 B: `MLP`
  - 单机: `sklearn.neural_network.MLPClassifier`
  - 分布式: `pyspark.ml.classification.MultilayerPerceptronClassifier`
  - 深度学习: PyTorch `nn.Sequential[Linear-ReLU-Dropout]` 三层

"任务一致、数据一致、评价一致、算法家族一致"是对比公平的前提。

### 4.3 关键创新(本 v2 新增)

**将 Spark 的使用场景拆为两段,形成分层对比:**

- **阶段 1 — 特征处理**: 从 `actigraphy` 原始加速度(数 GB)到 `feat_v2_biosensing`(MB 级)。对比 `pandas + chunk` vs `Spark DataFrame`。这里 Spark 期望有**明显优势**(数据量足够大)。
- **阶段 2 — 模型训练**: 从 `feat_v*.parquet`(MB 级)到训练好的模型。对比 `sklearn / Spark MLlib / PyTorch`。这里 Spark 期望**输给 sklearn**(启动开销 > 收益)。

报告结论: Spark 在 PIU 这类"轻模型 + 重预处理"任务上,应该把它放在 ETL/特征阶段,而不是模型训练阶段。这是课程项目最有价值的系统级洞见。

## 5. 项目 2 方案摘要

完整内容见 `04_plan_p2_v2.md`,此处只写要点:

### 5.1 目标

围绕同一 PIU 任务,贯穿完整 MLOps:

- 数据版本(DVC / git-lfs + hash)
- 特征版本(feat_v1/v2/v3)
- 模型选择(baseline → 深度 → 融合)
- 超参数优化(Optuna)
- 实验管理(MLflow Tracking + Artifacts)
- 模型注册(MLflow Model Registry,别名 baseline/candidate/champion/demo)
- 容器化(Dockerfile 两镜像)
- 轻量推理服务(FastAPI `/predict`)
- 双渠道发布(ModelScope 主 + HuggingFace Hub 镜像)

### 5.2 模型路线(从浅到深)

- **Baseline**:`Logistic Regression`、`CatBoost/XGBoost`、`MLP`(tabular only)
- **中等**: `1D CNN` on actigraphy 窗口、`Tabular MLP + biosensing stats`
- **进阶**: `late-fusion 双分支`(tabular branch + actigraphy 1D CNN branch,concat 后 MLP head)
- **可选**: `light Transformer`(若时间和 VRAM 允许)

### 5.3 主/辅指标

- 主: `QWK`(Kaggle 官方)
- 辅: `Macro-F1`、`Log Loss`
- 系统辅: 训练耗时 / 推理吞吐 / 参数量 / model size

## 6. 时间计划(周历)

| 周 | 日期 | 主要任务 | 验收(DoD) |
|---|---|---|---|
| W0 | 04-18~04-24 | 环境搭建 / 数据下载 / EDA | 三套 conda 可用;PIU 数据本地可读;磁盘占用 <40 GiB |
| W1 | 04-25~05-01 | P1 特征工程(feat_v1 tabular)+ sklearn baseline | LR / MLP 在 tabular 上跑出首份 QWK/Macro-F1 |
| W2 | 05-02~05-08 | Spark on actigraphy(feat_v2)+ PyTorch baseline | 三系统 LR/MLP 首轮对比表 |
| W3 | 05-09~05-15 | P1 消融 + 中期材料 | 中期 PPT 草案完成 |
| W4 | 05-16~05-22 | **中期答辩窗口** | 中期答辩通过 |
| W5 | 05-23~05-29 | P2 MLflow 接入 + baseline 迁移 | MLflow UI 可看 10+ runs,Registry 有 baseline |
| W6 | 05-30~06-05 | P2 深度模型 + Optuna 超参搜索 | 融合模型 QWK 较 baseline 提升 ≥0.03 |
| W7 | 06-06~06-12 | 模型注册 champion + Dockerfile + 发布材料 | ModelScope + HF 双仓可下载 |
| W8 | 06-13~06-19 | FastAPI `/predict` + 端到端 demo + 最终答辩准备 | 本地 demo 可跑 `curl` |
| W9 | 06-20~06-30 | **最终答辩** + 报告定稿 | 答辩完成 + 报告提交 |

关键锚点:

- `2026-05-20 前`: 中期材料定稿
- `2026-06-20 前`: 最终报告定稿 + 代码仓库封版

## 7. 团队分工(3 人)

### 成员 A — 数据与单机 + Spark

W0:
- 环境 `mlsys_cpu` 搭建
- PIU 数据下载 + 字段梳理 + 缺失统计

W1-W2:
- `feat_v1_tabular` 建立(缺失值处理、标准化、编码)
- `feat_v2_biosensing` 建立(actigraphy 滑窗 + 统计特征)
- **pandas vs Spark** 对比实验(W2 重点)
- sklearn LR/MLP baseline

W3-W4:
- P1 消融实验(feat_v1 vs feat_v2 vs feat_v3 融合)
- 中期汇报资源数据准备

W5-W9:
- 保持 Spark/sklearn pipeline 稳定,配合 B/C 出最终报告

### 成员 B — 深度学习

W0-W1:
- 环境 `mlsys_gpu_local` / `mlsys_gpu_remote` 搭建与验证
- PyTorch 跑通 `tabular MLP` baseline

W2-W3:
- `1D CNN on actigraphy` baseline
- 与 sklearn MLP 对齐结果(跨系统同算法公平性)

W5-W6:
- `late-fusion 双分支`
- Optuna 超参搜索(跑在 4090)
- 可选: light Transformer

W7-W9:
- 最佳模型定稿
- 推理脚本与演示用例

### 成员 C — MLOps + 发布

W0-W1:
- 搭 MLflow server(本地 SQLite + artifact 目录)
- DVC 或 git-lfs 初始化
- `Makefile` 串起 pipeline

W2-W4:
- MLflow 规约文档(Tracking / Artifact / Registry 的 tag、label 约定)
- 中期 PPT 的 MLOps 章节

W5-W7:
- Model Registry 管理(baseline → candidate → champion)
- Dockerfile(CPU 推理 / GPU 训练两镜像)
- FastAPI `/predict` 推理服务
- ModelScope 仓库初建
- HuggingFace Hub 镜像

W8-W9:
- 端到端 demo 脚本
- 最终答辩 PPT MLOps 部分

### 两人降级方案

- A+B 合并(数据 + 传统 + PyTorch),C 独立负责 MLOps + 评估 + 汇报材料
- 降级会削弱 Optuna 超参扫描规模和 Transformer 可选项

## 8. 风险与应对(摘要,完整版见 `06_risk_and_eval_v2.md`)

| # | 风险 | 应对 |
|---|---|---|
| R1 | 远程 4090 使用窗口无保证 | 三级 GPU fallback (4090 → Kaggle Notebook → AutoDL/Colab Pro) |
| R2 | 5060 Ti sm_120 在 stable 未 land | nightly 2.10+ 通道备用;CPU 训练兜底(仅 MLP 以下规模) |
| R3 | 磁盘 66 GiB 不够 | 15 GiB 预留;超预算切 WISDM |
| R4 | Kaggle API 国内连接问题 | 镜像 fallback + 手动下载 |
| R5 | actigraphy 缺失多 | 设计为"可选加强分支",支持单分支推理 |
| R6 | Spark 在训练阶段反而慢 | 报告直接给出该结论,阐明 Spark 的真实适用场景(特征阶段),这是深度洞见而非 bug |
| R7 | ModelScope 发布模板不支持双输入 | 用 `custom pipeline`,W7 预留 3-5 天 |
| R8 | 中期答辩日期变化 | 周历有缓冲,可整体前移一周 |

## 9. 预期成果

- 项目 1:
  - 三系统 LR/MLP 统一对比表
  - Spark 特征处理阶段 vs pandas 的真实数据量级对比(本 v2 亮点)
  - 系统设计决策分析报告
- 项目 2:
  - 分层模型矩阵(baseline / 1D CNN / 融合)
  - MLflow 追踪记录 + Registry 管理的 4 个别名(baseline/candidate/champion/demo)
  - Dockerfile + FastAPI `/predict` 服务
  - ModelScope 主仓 + HuggingFace Hub 镜像
- 共同:
  - 可复现实验脚本(含 `Makefile`、requirements-pinned、seed=42)
  - 中期 + 最终汇报 PPT 与书面报告
  - `Child-Mind-PIU-Risk-Identifier-v1.0` 模型 card

## 10. 参考资料

- Kaggle PIU 竞赛: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use
- Child Mind Institute HBN 项目: https://childmind.org/our-research/center-for-the-developing-brain/healthy-brain-network/
- WISDM 官方: https://www.cis.fordham.edu/wisdm/dataset.php
- PyTorch 安装(cu128): https://pytorch.org/get-started/locally/
- PyTorch sm_120 追踪: https://github.com/pytorch/pytorch/issues/164342
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- ModelScope: https://github.com/modelscope/modelscope
- HuggingFace Hub 文档: https://huggingface.co/docs/hub/
- 国科大一站式开题/中期通知: https://onestop.ucas.ac.cn/home/info/16edeb59-0332-4c3d-9f11-99b73c6a0ed0
- 人工智能学院通知: https://aipt.ucas.ac.cn/index.php/zh-cn/lunwentongzhi/6335-2026

## 11. 修订记录

- `v2 draft | 2026-04-18`:把 v1 的 HAR 主线调整为 PIU 主线;锁环境 `torch 2.11 / nightly 2.10+ + cu128`;统一评价指标 P1=Macro-F1/P2=QWK;周历化时间计划;明确三人分工与两人降级;新增双发布通道;与 `cc/` 目录其它 5 份文件配套。

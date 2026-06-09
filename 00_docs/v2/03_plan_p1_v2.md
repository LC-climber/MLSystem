# 项目 1 优化版方案 — 多系统 PIU 风险识别算法对比 v2

- 项目编号: `MLSYS-2026S-P1-COMPARE-PIU`
- 课程名称: `机器学习系统`
- 对应作业: `项目实践及演示汇报-1`
- 项目题目: `多系统问题性互联网使用风险识别算法对比: 单机、分布式与深度学习系统的分层性能分析`
- 数据来源: `Kaggle Child Mind Institute — Problematic Internet Use`
- 原版本: `00_docs/v1/plans/plan_p1_childmind_piu_v1.md`(2026-04-16)
- 文档版本: `v2`
- 日期: `2026-04-18`
- 团队成员: A / B / C(姓名待填)
- 指导教师: `待填写`

## 0. 相对 v1 的改动点

| # | v1 | v2 | 原因 |
|---|---|---|---|
| 1 | Spark 做模型训练(3000 样本),必输给 sklearn | Spark **分两段**:阶段 1 在 actigraphy 预处理阶段(数 GB)/ 阶段 2 才是模型训练 | 只跟 sklearn 比训练必然败北,拆成两段后 Spark 在特征阶段真有价值 |
| 2 | 指标三选一 `QWK / Macro-F1 / Accuracy`,未锁主 | 主 **Macro-F1**,辅 QWK / Balanced Accuracy | 答辩有公共尺子;Macro-F1 不被 majority class 主导 |
| 3 | 特征版本 "tabular-only / biosensing-only / fused" 提了但未规范 | 正式命名 `feat_v1_tabular` / `feat_v2_biosensing` / `feat_v3_fusion` 并记入 MLflow | 跨成员可引用 |
| 4 | 方案 A/B/C 三种并列,没有 done 标准 | 每条路径给 done 标准 + 预估周次 | 答辩可答"完成度" |
| 5 | 缺硬件可行性的定量论证 | 给磁盘/VRAM/时间三项估算(见 `05_runbook_v2.md`) | 可提前预警 |
| 6 | 风险应对不具体 | 硬兜底直接切 WISDM,给切换 SOP | 真能落地 |
| 7 | 未使用统一 seed | 全局 `seed=42`,跨系统一致 | 可复现 |

## 1. 摘要

本项目面向青少年问题性互联网使用(PIU)风险识别任务,基于 Kaggle `Child Mind Institute — Problematic Internet Use` 竞赛数据,构建一套面向 `单机 sklearn / 分布式 Spark / 深度学习 PyTorch` 的统一对比实验。

与一般课程项目"只在模型训练阶段比系统"不同,本方案将 Spark 的考察分为两段:**(1) actigraphy 原始加速度时序 → 特征矩阵的预处理阶段** 和 **(2) 特征矩阵 → 训练模型的训练阶段**。这样设计的原因是 PIU 训练集仅约 3000 样本,在训练阶段 Spark 的启动开销必然大于收益;但 actigraphy 原始时序是数 GB 级,预处理阶段 Spark 相对 pandas 有真实优势。本方案因此回答一个更有教学价值的问题: **"分布式框架该放在机器学习 pipeline 的哪一段?"**

本项目在 `scikit-learn / Spark MLlib / PyTorch` 上实现 `Logistic Regression` 和 `MLP` 两类算法,评估模型指标(主 Macro-F1 + QWK/Balanced Accuracy)、系统效率(训练/推理耗时、吞吐、RSS)、工程复杂度等维度,输出可复现脚本、跨系统对比表格、中期汇报 PPT 和书面分析报告。

**关键词**: `机器学习系统`、`Kaggle PIU`、`多系统对比`、`Spark ETL`、`PyTorch`

## 2. 研究背景与意义

PIU 风险识别涉及青少年认知与行为健康,其数据与一般玩具数据集的显著差异体现在:

- **异构**: 人口统计 + 临床问卷 + 体测 + 可穿戴加速度计时序
- **稀缺且不平衡**: 总参与者仅约 3000,actigraphy 覆盖率与长度参差
- **真实世界 ML 系统挑战**: 从原始信号到特征再到模型,整条数据链条都有可讨论空间

从《机器学习系统》课程视角,这类任务的价值在于:

- 允许把"单机 / 分布式 / 深度学习"三类系统放到同一任务中对比
- 允许讨论"特征工程阶段" vs "模型训练阶段"谁应该用分布式
- 允许对比"传统机器学习系统的工程简洁性"和"深度学习系统的端到端灵活性"

## 3. 任务理解与数据

### 3.1 数据结构(已核实)

Kaggle 竞赛数据包含两大部分:

| 模态 | 内容 | 规模 | 完整率 |
|---|---|---|---|
| Tabular | 人口统计、家庭、心理问卷、体测、临床测量 | ~3000 参与者 × ~80 列 | 多数字段完整,部分问卷有缺失 |
| Actigraphy | 可穿戴加速度计原始时序,通常为数周 | 约 10-20 GB 解压后 parquet | **覆盖率约 30-60%**(很多参与者无 actigraphy) |

### 3.2 标签

- 目标: **Severity Impairment Index (SII)**,基于 `Internet Addiction Test (IAT)` 派生的 4 级有序分类
- 官方评分指标: **Quadratic Weighted Kappa (QWK)**

### 3.3 数据切分

- 按 **participant_id 分层 K-Fold(K=5)**,确保来自同一参与者的样本不跨 fold
- 固定 `seed=42`
- 最后 report 使用 5-fold CV 均值 ± 标准差

## 4. 研究目标

1. 建立 PIU 统一的数据清洗、缺失处理、特征表示规范
2. 在 `sklearn / Spark / PyTorch` 上实现 `LR` 和 `MLP`,保证"任务/数据/算法/评价"一致
3. **关键目标**: 定量对比 Spark 在 (a) 特征预处理阶段 和 (b) 模型训练阶段 两个位置上的性能与代价
4. 形成可复现实验脚本 + 跨系统对比表 + 可视化图表
5. 为项目 2 MLOps 提供 baseline 与特征版本基础

## 5. 研究内容

### 5.1 统一数据切分协议

- StratifiedGroupKFold(K=5),group=participant_id,stratify=SII
- 训练 / 验证 4:1
- 固定 seed=42,记录 fold assignment 为 `data/splits/stratified_group_kfold_seed42.csv`

### 5.2 特征版本(3 档)

| 版本 | 内容 | 文件 | 大小估算 |
|---|---|---|---|
| `feat_v1_tabular` | 仅 tabular,缺失用列中位数/众数填补,类别 one-hot 或 target encoding | `feat_v1__seed42.parquet` | ~5 MB |
| `feat_v2_biosensing` | tabular + actigraphy 滑窗统计(均值/方差/分位数/夜间时段 IM) | `feat_v2__{cpu/spark}__seed42.parquet` | ~20 MB |
| `feat_v3_fusion` | tabular + biosensing 统计 + actigraphy 窗口级嵌入(1D CNN 产出) | `feat_v3__seed42.parquet` | ~50 MB |

`feat_v2` 是本项目 **Spark 价值的核心试验场**,必须同时产出 `feat_v2__cpu.parquet` 和 `feat_v2__spark.parquet` 用于对比。

### 5.3 系统对比对象

- 单机: `scikit-learn`
- 分布式: `Spark MLlib`(本机伪分布式,`--master local[20]`)
- 深度学习: `PyTorch`

### 5.4 算法家族(同算法跨系统对齐)

#### 算法 A — Logistic Regression

- sklearn: `sklearn.linear_model.LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced')`
- Spark: `pyspark.ml.classification.LogisticRegression(maxIter=1000, regParam=0.0, elasticNetParam=0.0)`
- PyTorch: `nn.Linear(in_dim, num_classes)` + `CrossEntropyLoss(weight=class_weights)`,Adam lr=1e-3

#### 算法 B — MLP

- sklearn: `MLPClassifier(hidden_layer_sizes=(128,64), activation='relu', early_stopping=True, random_state=42)`
- Spark: `MultilayerPerceptronClassifier(layers=[in, 128, 64, num_classes])`
- PyTorch: `nn.Sequential(Linear→ReLU→Dropout(0.2)→Linear→ReLU→Dropout(0.2)→Linear)`,AdamW lr=1e-3,EarlyStopping patience=10

**对齐公平性**: 三系统使用相同的 feat_v1/v2,相同 CV 折,相同 class_weight 策略,相同 seed。超参不调优,只做"统一条件的横向对比"。

## 6. 技术路线(流程图文字版)

```
[Kaggle CLI 下载] 
    ↓
[data/raw/ (12 GiB)] —— checksum ——
    ↓
[数据清洗与 EDA (成员 A, W0-W1)]
    ↓
[feat_v1_tabular (W1)] ——→ sklearn/Spark/PyTorch LR & MLP (W1-W2) ——→ 对比表 1
    ↓
[feat_v2_biosensing 双路径 (W2)]
    ├── pandas + chunk (mlsys_cpu)
    └── Spark DataFrame (mlsys_cpu, local[20])
          ↓
        [耗时 / RSS / 输出一致性对比] ← ★ 本项目关键实验 ★
    ↓
[feat_v2] ——→ sklearn/Spark/PyTorch LR & MLP ——→ 对比表 2
    ↓
[feat_v3_fusion (W3, 可选)] ——→ 消融
    ↓
[P1 最终对比报告 + 中期材料 (W3-W4)]
```

## 7. 实验设计

### 7.1 评价协议

- **主指标**: `Macro-F1`(对类别不平衡稳健)
- **辅指标**: `QWK`(Kaggle 官方)、`Balanced Accuracy`
- **系统指标**:
  - 训练总耗时(wall-clock,不含环境启动)
  - 单 epoch 时间(只对 PyTorch)
  - 单样本推理延迟(μs,取 1000 次均值)
  - 推理吞吐(samples/s)
  - 峰值 RSS(通过 `psutil.Process().memory_info().rss` 采样)
  - 峰值 GPU memory(`torch.cuda.max_memory_allocated()`)
  - 模型文件大小(MB)
  - 特征处理端到端时间(pandas vs Spark)
  - Spark shuffle 写量(从 Spark UI 读取)

### 7.2 对比表结构(最终报告)

**表 1 — 特征处理阶段对比(pandas vs Spark)**

| feat 版本 | 工具 | 耗时(s) | 峰值 RSS(GB) | 输出 MD5 | 一致性 |
|---|---|---|---|---|---|
| feat_v2 | pandas+chunk | T1 | M1 | hash1 | ref |
| feat_v2 | Spark local[20] | T2 | M2 | hash2 | 与 ref 等价性(列级 diff <1e-6) |

**表 2 — 模型训练阶段对比(三系统 × 两算法 × 两特征版本)**

| 特征 | 系统 | 算法 | Macro-F1 | QWK | Bal. Acc | 训练耗时 | 推理延迟 | 峰值内存 | 模型大小 |
|---|---|---|---|---|---|---|---|---|---|
| v1 | sklearn | LR | ... | | | | | | |
| v1 | Spark | LR | ... | | | | | | |
| v1 | PyTorch | LR | ... | | | | | | |
| v1 | sklearn | MLP | ... | | | | | | |
| v1 | Spark | MLP | ... | | | | | | |
| v1 | PyTorch | MLP | ... | | | | | | |
| v2 | (同上 6 行) | | | | | | | | |

共 12 行数据 + 报告文字分析。

### 7.3 消融实验

- A1: 缺失值填补策略(中位数 vs KNNImputer vs MissForest)对 LR 影响
- A2: 标准化前后对 sklearn MLP 的影响
- A3: `class_weight` 开/关对 Macro-F1 的影响
- A4: tabular-only vs tabular+biosensing
- A5: actigraphy 覆盖率(30% / 50% / 全体)对融合特征的影响
- A6: Spark `local[4]` / `local[8]` / `local[20]` 并行度扫描,绘制耗时曲线

### 7.4 可视化

- 跨系统雷达图(Macro-F1 / QWK / 训练耗时倒数 / 推理吞吐 / 内存倒数 / 模型大小倒数)
- Spark 并行度扫描曲线
- 混淆矩阵 × 6(三系统 × 两算法)
- feat_v2 pandas vs Spark 的 lineage 对比图

## 8. 资源与环境

### 8.1 本地

- `mlsys_cpu`:pandas / pyspark / scikit-learn
- `mlsys_gpu_local`:5060 Ti,主要用于 PyTorch 调试(sm_120 需 nightly)

### 8.2 远程

- `mlsys_gpu_remote`:4090 stable

本项目 P1 **大部分在本地完成**(CPU 系统对比是主戏);远程 GPU 仅在 PyTorch MLP 需要 GPU 加速时短暂使用。

## 9. 多场景实施方案

### 9.1 方案 A — 标准方案(推荐,优先执行)

适用条件: 远程 4090 可用 ≥10 小时,磁盘 < 40 GiB,actigraphy 可正常解析

内容:
- LR + MLP 两算法
- feat_v1 + feat_v2 两特征版本
- 三系统全部完成
- feat_v3 fusion 仅做一条展示路径(不计入严格对比)

DoD:
- 跨系统对比表 2(12 行)完整
- 特征处理对比表 1 完整
- 雷达图 + 混淆矩阵 + 并行度曲线

### 9.2 方案 B — 资源受限方案

适用条件: 远程 4090 不稳定,或 actigraphy 解析遇困难

内容:
- 只做 `feat_v1_tabular`
- LR + MLP 两算法
- 三系统全部完成
- Spark 仅做伪分布式对照

DoD: 对比表 2 的 feat_v1 部分(6 行)

### 9.3 方案 C — 硬兜底(切 WISDM)

触发: W1 末仍未在 PIU 上跑通任一 baseline,或磁盘超 55 GiB,或 actigraphy OOM

切换内容:
- 数据: PIU → WISDM(~1 GiB 原始,~3 GiB 加工)
- 任务: SII 分类 → 6 类 HAR 分类
- 指标: 主 `Macro-F1`,辅 `Accuracy` / `Balanced Accuracy`
- Spark 在 WISDM 上直接做模型训练对比(298 万样本,有意义)
- 其余框架不变

切换 SOP 见 `06_risk_and_eval_v2.md` §6。

## 10. 可行性

### 10.1 可行性来源

- 数据公开可获得,有多份镜像
- 单机/分布式/深度学习三类工具链成熟
- 当前硬件足以支撑 baseline 与正式实验(见 `05_runbook_v2.md` 具体预算)
- 同主题已有若干竞赛公开解法可参考

### 10.2 主要困难

- Actigraphy 原始数据量可能大于预期(视参与者时长)
- 缺失值处理策略对结果影响大,需严控只在训练集上 fit imputer
- Spark 在本机伪分布式下的表现需合理解读,不能把"本机 Spark 慢"结论泛化到"Spark 慢"

### 10.3 预期时间消耗(粗估)

- EDA 与 feat_v1 搭建: 2 人天(成员 A)
- feat_v2 pandas 版 + Spark 版: 3 人天(成员 A)
- 三系统 LR 实现: 2 人天(A+B)
- 三系统 MLP 实现: 2 人天(A+B)
- 消融: 3 人天
- 中期材料: 3 人天

合计约 `15 人天`,3 人团队 ≈ 5-7 自然天纯工作时间,配合 W0-W4 5 周有充分缓冲。

## 11. 预期创新点

- 将 PIU 任务转化为"特征阶段 Spark"与"训练阶段 Spark"分层对比,回答"分布式框架放在 pipeline 哪一段"这一更具普适性的教学问题
- 在 tabular 任务上给出 Spark 本机伪分布式的并行度-耗时曲线,可作课程横向案例库的参考数据

## 12. 进度安排

| 周 | 成员 A | 成员 B | 成员 C |
|---|---|---|---|
| W0 | 环境 `mlsys_cpu` / 数据下载 / EDA | `mlsys_gpu_local` 验证 5060 Ti / 远程 4090 验证 | MLflow server / DVC 初始化(P2 提前准备) |
| W1 | feat_v1_tabular / sklearn LR+MLP | PyTorch tabular MLP baseline | MLflow 跑通记录 feat_v1 实验 |
| W2 | feat_v2 pandas + Spark 两路径 | 对齐 PyTorch 在 feat_v2 的指标 | Spark job 结果记录 MLflow;整理中期 MLOps 章节 |
| W3 | 消融 A1-A6 / 对比表 2 定稿 | 深度模型 feat_v2 微调 | 可视化脚本 / 中期 PPT 汇总 |
| W4 | 中期答辩材料 + 书面报告 P1 部分 | 支持演示 | 中期 PPT 收口 |

## 13. 预期成果

- `src/data/preprocess_tabular.py`、`src/data/preprocess_actigraphy_{pandas,spark}.py`
- `src/models/sklearn_baselines.py`、`src/models/spark_baselines.py`、`src/models/torch_baselines.py`
- `src/experiments/run_p1_systemwise.py`(一键跑 12 行对比)
- `notebooks/p1_eda.ipynb`、`notebooks/p1_ablation.ipynb`
- `reports/P1/` 目录下的对比表 1、表 2、雷达图、混淆矩阵、并行度曲线
- 中期 PPT 草案(`00_docs/midterm_slides_outline_v1.md`)

## 14. 风险与应对(P1 专属,通用风险见 `06_risk_and_eval_v2.md`)

| # | P1 专属风险 | 应对 |
|---|---|---|
| P1-R1 | Spark 在 feat_v2 上仍输给 pandas(数据量不够) | 报告直接阐明"数据量拐点"的观察;补充 actigraphy 10x 合成放大的扩展实验作对照 |
| P1-R2 | sklearn MLP 与 PyTorch MLP 在同 feat 上 Macro-F1 差异 >0.05 | 先排查 seed、初始化、优化器;若仍无法对齐,加实验说明"默认超参下两者差异来源" |
| P1-R3 | Spark MLlib 的 MultilayerPerceptronClassifier 默认 optimizer 与 sklearn 不同导致不公平 | 接受差异并在报告中明确,必要时加 note |
| P1-R4 | actigraphy 覆盖不足导致 feat_v2 大量 NaN | 分层实验:仅对有 actigraphy 的子集做 feat_v2,tabular 部分保留全体 |

## 15. 参考资料

- Kaggle PIU: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use
- PIU 获胜方案公开讨论: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/discussion
- Healthy Brain Network: https://childmind.org/our-research/center-for-the-developing-brain/healthy-brain-network/
- PIU 竞赛数据说明论文: https://www.sciencedirect.com/science/article/pii/S2214782925000648
- PySpark MLlib Classification: https://spark.apache.org/docs/latest/api/python/reference/pyspark.ml.html
- sklearn LogisticRegression: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- PyTorch: https://pytorch.org/docs/stable/index.html

## 16. 修订记录

- `v2 | 2026-04-18`: 重构 Spark 使用位置为"特征阶段 + 训练阶段"两段对比;锁 Macro-F1 主指标;特征版本正式命名;给每方案 done 标准;新增 WISDM 硬兜底切换 SOP 引用;与 cc/ 目录其它 5 份文件对齐。

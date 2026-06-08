# MLsystem 项目开发日志

## 项目信息

- **项目名称**: MLsystem - 机器学习系统课程项目
- **数据集**: Child Mind Institute - Problematic Internet Use (PIU)
- **任务类型**: 多分类 (4类: None, Mild, Moderate, Severe)
- **评估指标**: Quadratic Weighted Kappa (QWK)
- **开发周期**: W0-W8 (8周)
- **开发环境**: Linux (Ubuntu), RTX 5060 Ti, Python 3.11

---

## 2026-06-08 - P2 阶段 1: MLflow 深度集成启动

### 背景

P1 中期汇报已完成(2026-06-03)，当前进入 P2 MLOps 实践阶段。P2 目标是构建完整的 MLOps 闭环，包括 MLflow Registry、Optuna 超参优化、FastAPI 推理服务、Docker 容器化和双渠道模型发布。

### 当前阶段目标

实施 P2 阶段 1: MLflow 深度集成，建立完整的实验追踪和模型注册体系。

### 新增模块

#### 1. MLflow 工具包 (`src/mlflow_utils/`)

| 文件 | 功能 | 关键接口 |
|------|------|----------|
| `tracking.py` | 增强的实验追踪 | `log_experiment()`, `log_cv_results()`, `log_confusion_matrix()`, `log_feature_importance()`, `log_training_curve()`, `log_pr_curve()` |
| `registry.py` | Model Registry 管理 | `init_registry()`, `register_model()`, `set_alias()`, `get_model_by_alias()`, `promote_model()`, `list_models_by_tag()`, `get_model_metadata()` |
| `artifacts.py` | Artifact 管理 | `save_model_summary()`, `create_model_card()`, `save_inference_script()`, `save_input_example()` |

**设计要点**:
- 统一的实验记录接口，自动记录参数、指标、可视化
- 4 个模型别名体系: `baseline`(P1 最佳)、`candidate`(Optuna 当前最佳)、`champion`(正式发布)、`demo`(轻量演示版)
- 自动生成 Model Card、推理脚本等发布材料
- 支持模型晋升逻辑 (candidate → champion)

#### 2. Baseline 注册脚本 (`scripts/register_baseline.py`)

**功能**:
- 从 P1 报告 CSV 中自动选择最佳模型 (按 QWK 排序)
- 在 MLflow 中搜索对应的 run
- 注册到 Model Registry 并设置 `baseline` 别名
- 保存 baseline 信息到 `models/baseline_info.json`

**使用方式**:
```bash
# 查看选择结果（不实际注册）
python scripts/register_baseline.py --dry-run

# 实际注册 baseline
python scripts/register_baseline.py
```

### 代码质量检查

```bash
python -m compileall -q src/mlflow_utils/ scripts/register_baseline.py
```

✓ 所有文件语法检查通过。

### 下一步计划

1. **验证 MLflow 工具**: 重跑一个 P1 实验，验证增强的 tracking 功能
2. **注册 baseline**: 运行 `register_baseline.py`，建立对比基准
3. **启动 Optuna 集成**: 开发 `run_p2_optuna.py`，集成超参数优化

### 预期产物

- MLflow UI 中出现 `piu-risk` 注册模型
- `baseline` 别名指向 P1 最佳模型
- 增强的可视化 (混淆矩阵、PR 曲线、训练曲线)

---

## 2026-06-03 - P1 中期汇报材料

### 目标

明天需要汇报,因此将 P1 已完成实验整理为可直接使用的报告、PPT 和动画讲解页。

### 新增材料

| 类型 | 路径 | 说明 |
|---|---|---|
| 报告 Markdown | `00_docs/P1_MIDTERM_REPORT.md` | 按汇报叙事组织:问题、协议、Table 1、Table 2、A5、A6、结论与风险 |
| 讲稿提示 | `00_docs/P1_MIDTERM_TALK_TRACK.md` | 8-10 分钟逐页讲法、重点句和时间预算 |
| 答辩 Q&A | `00_docs/P1_MIDTERM_QA.md` | Spark、feat_v2、A5/A6、公平性、P2 衔接等追问口径 |
| PPTX | `reports/p1_midterm_slides.pptx` | 13 页,封面 + 10 页正文 + 2 页备用附录 |
| 动画 HTML | `reports/p1_midterm_explainer.html` | 独立 HTML,带步骤切换/自动播放/数据包动画,解释 Spark 在特征/ETL 阶段的机制 |
| PPT 构建脚本 | `scripts/build_p1_midterm_ppt.py` | 从 `reports/figures/` 重新生成 PPTX |

### PPT 结构

1. P1 中期汇报封面
2. 研究问题与公平协议
3. 数据事实:Spark 有机会但 v2 覆盖受限
4. Table 1:特征阶段 pandas vs Spark
5. Table 2:模型质量没有因 feat_v2 稳定提升
6. 系统成本:Spark 不适合小表格训练和单样本推理
7. A5:覆盖率解释 feat_v2 为什么没有稳定收益
8. A6:Spark 并行度不是越高越快
9. 代表性混淆矩阵:类别 3 是指标不稳定来源
10. 汇报主线:Spark 价值在哪里
11. 结论与下一步
12. Appendix A:答辩 Q&A 速记
13. Appendix B:复现命令与材料路径

### HTML 动画页

`reports/p1_midterm_explainer.html` 是无外部依赖的单文件页面:
- 顶部是可自动播放的 6 步 pipeline 动画。
- 中段复用 6 张核心 SVG 图。
- 重点解释从 tabular / actigraphy 到 pandas reference / Spark candidate / feat_v2 / Table 2 结论的因果链。

### 环境变更

为生成 PPTX 安装并记录:
- `python-pptx==1.0.2`
- `lxml==6.1.1`
- `xlsxwriter==3.2.9`

已补入 `envs/pinned_openpi_311_mlsys.txt`。

### 验证

- `python scripts/build_p1_midterm_ppt.py` 成功生成 PPTX。
- 使用 `python-pptx` 回读 `reports/p1_midterm_slides.pptx`,确认 13 页。
- HTML 引用的 6 张 SVG 图均存在。
- `python -m compileall -q src scripts` 通过。

### 当前进度同步

- P1 中期汇报材料已可直接使用,并已补讲稿提示与答辩 Q&A。
- 下一步建议暂停 P1 新实验,转为演练汇报。

---

## 2026-06-03 - W3 核心可视化

### 目标

把 P1 已完成的主表、A5、A6 和 feat_v2 lineage 固化为可直接用于中期汇报/论文的图。

### 新增脚本

新增 `src/experiments/run_p1_visualizations.py`:
- 读取 `reports/p1_systemwise_table2.csv`、`reports/p1_ablation_a5_coverage.csv`、`reports/p1_ablation_a5_fold_coverage.csv`、`reports/p1_spark_parallelism_feat_v2.csv`。
- 输出 SVG + PNG 到 `reports/figures/`。
- 为代表性混淆矩阵重跑 `sklearn LR` 的 v1/all 与 v2/all 5-fold out-of-fold 预测,不改变已有 Table 2 指标。
- 在脚本中设置 `MPLCONFIGDIR=/tmp/mlsystem-matplotlib`,避免 sandbox 下 Matplotlib home config 不可写的 warning。

执行命令:

```bash
python -m src.experiments.run_p1_visualizations
```

### 产物

| 文件 stem | 内容 |
|---|---|
| `p1_table2_metric_bars` | Macro-F1 / QWK / Balanced Accuracy 的 v1 vs v2 跨系统对比 |
| `p1_system_costs` | `feat_v2/all` 训练耗时与单行推理延迟(log scale) |
| `p1_a6_spark_parallelism` | Spark `local[4]/[8]/[20]` wall time 与进程树 RSS |
| `p1_a5_coverage` | actigraphy fold 覆盖率 + class 分布,标出 fold 4 无 class 3 |
| `p1_confusion_sklearn_lr` | `sklearn LR` v1/all 与 v2/all out-of-fold 混淆矩阵 |
| `p1_feature_lineage` | pandas streaming 与 Spark applyInPandas 的 feat_v2 特征 lineage |

每个 stem 均生成 `.svg` 与 `.png`,共 12 个文件。

### 验证

- `python -m compileall -q src scripts` 通过。
- `python -m src.experiments.run_p1_visualizations` 成功生成全部图。
- PNG 像素非空检查通过。
- 人工抽查 `p1_table2_metric_bars`、`p1_a5_coverage`、`p1_a6_spark_parallelism`、`p1_confusion_sklearn_lr`、`p1_feature_lineage`:布局清晰,无明显裁切;lineage 初版右侧裁切已修正后重生成。

### 当前进度同步

- W3 已完成 A5、A6 与核心可视化。
- P1 已具备中期材料所需的核心证据链:主表结果、Spark 特征阶段对比、覆盖率解释、并行度曲线、系统开销图和 lineage 图。
- 下一步可选两条:继续补 A1-A4 轻量消融,或转入中期报告/PPT 骨架整理。

---

## 2026-06-03 - W3 A5:actigraphy 覆盖率/子集分析

### 目标

解释 `feat_v2_biosensing` 在 Table 2 主表中没有稳定提升的原因:是真实 actigraphy 信号无效,还是覆盖率不足和子集类别稀疏导致收益被稀释。

### 新增脚本

新增 `src/experiments/run_p1_ablation_a5_coverage.py`:
- 读取已完成的 `reports/p1_systemwise_table2.csv` 与 `reports/p1_systemwise_feat_v2_actigraphy.csv`。
- 从 `feat_v2__cpu__seed42.parquet` 和原 5-fold assignment 计算 actigraphy 覆盖率、fold 覆盖分布和 class 分布。
- 输出同协议主表 delta(`v2/all - v1/all`)与 actigraphy 子集补充结果。

执行命令:

```bash
python -m src.experiments.run_p1_ablation_a5_coverage
```

### 产物

- `reports/p1_ablation_a5_coverage.csv` — 三系统 x 两算法的 A5 汇总表。
- `reports/p1_ablation_a5_fold_coverage.csv` — 5-fold 覆盖率与 class 分布表。

### 覆盖率事实

| 口径 | 覆盖数 | 覆盖率 |
|---|---:|---:|
| 全体 feature 行 | 996 / 3960 | 25.2% |
| 有标签 CV 样本 | 996 / 2736 | 36.4% |

5-fold actigraphy 子集分布:

| fold | all n | actigraphy n | coverage | actigraphy class 3 |
|---:|---:|---:|---:|---:|
| 0 | 547 | 200 | 36.6% | 3 |
| 1 | 548 | 215 | 39.2% | 4 |
| 2 | 547 | 200 | 36.6% | 1 |
| 3 | 547 | 192 | 35.1% | 2 |
| 4 | 547 | 189 | 34.6% | 0 |

### 指标解释

同协议主表(`v2/all - v1/all`)下:
- LR 三系统 Macro-F1 均略降:`sklearn -0.003`,`spark -0.019`,`pytorch -0.002`。
- MLP 结果混合:`sklearn +0.005`,`spark +0.033`,`pytorch -0.002`;只有 Spark MLP 明显上升,不足以支持"feat_v2 稳定提升"。
- QWK 多数下降,只有 PyTorch LR 轻微上升(`+0.002`)和 Spark MLP 上升(`+0.017`)。

子集结果解释:
- `v2/actigraphy` 只保留 996 个有真实 actigraphy 的标注样本,不是 Table 2 主协议。
- fold 4 的 actigraphy 子集没有 class 3 验证样本,因此该表只能作为覆盖率敏感性/补充证据。
- 论文/汇报口径:actigraphy 特征工程与 Spark 等价性已成立,但当前数据覆盖率与类别稀疏限制了它对主表指标的稳定贡献。

### 当前进度同步

- W3 已完成 A5 与 A6 两个关键消融。
- 下一步建议转向可视化:Table 2 跨系统图、A6 并行度曲线、A5 覆盖率图、代表性混淆矩阵和 pandas/Spark lineage 图。

---

## 2026-06-03 - W3 A6:Spark 并行度扫描

### 目标

完成 P1 W3 消融 A6:对 `feat_v2` actigraphy Spark 特征阶段扫描 `local[4]` / `local[8]` / `local[20]`,判断本机 local mode 下增加并行度是否改善耗时。

### 新增脚本

新增 `src/experiments/run_p1_spark_parallelism.py`:
- 复用 `run_p1_feature_stage.py` 的进程树 RSS 采样、逻辑 hash、NaN 感知等价性校验和 MLflow fallback。
- 每完成一个 Spark master 即写一次 `reports/p1_spark_parallelism_feat_v2.csv`,避免长任务中断丢失已完成结果。
- 失败时保留 `status=failed` 与 `error_message`,便于把 OOM/GC 等系统失败纳入报告。

执行命令:

```bash
python -m src.experiments.run_p1_spark_parallelism \
  --masters local[4],local[8],local[20] \
  --mlflow
```

HTTP MLflow server 未运行时继续 fallback 到本地 `sqlite:///mlruns.db`;本次已写入 `spark_parallelism_local_4` / `local_8` / `local_20` runs。

### 结果

产物:`reports/p1_spark_parallelism_feat_v2.csv`。

| Spark master | wall(s) | peak RSS(GB) | rows x cols | act rows | logical hash | 等价性 |
|---|---:|---:|---|---:|---|---|
| `local[4]` | 115.48 | 12.42 | 3960 x 147 | 996 | `5530ecc5f44fda5247629879523c3d38` | `max_abs_diff=5.68e-14`;NaN equal |
| `local[8]` | 138.12 | 13.29 | 3960 x 147 | 996 | `5530ecc5f44fda5247629879523c3d38` | `max_abs_diff=1.14e-13`;NaN equal |
| `local[20]` | 161.53 | 18.00 | 3960 x 147 | 996 | `5530ecc5f44fda5247629879523c3d38` | `max_abs_diff=1.14e-13`;NaN equal |

### 结论

- 三个并行度均与 pandas reference 等价,因此 A6 只比较系统资源/调度效果。
- 当前 `groupBy(id).applyInPandas` 精确聚合路径在本机最佳为 `local[4]`;`local[8]` 与 `local[20]` 反而更慢。
- `local[20]` 相比 `local[4]` 慢约 40%,峰值 RSS 从 12.42 GB 升到 18.00 GB。
- 解释:该路径更受 shuffle/序列化/I/O、Python worker 调度和每组 pandas reducer 尾部任务影响,不是单纯 CPU core 数不足。报告中可据此说明"Spark 并行度不是越高越好;local mode 需要实测拐点"。

### 当前进度同步

- P1 主线(多系统算法对比)已完成:Table 1 + Table 2 + v2 actigraphy 子集补充表均已固化。
- W3 已完成 A6;下一步优先推进 A5 覆盖率/子集分析说明,再做 A1-A4 或可视化(雷达图、混淆矩阵、lineage)。

---

## 2026-06-02 - W2 收口:feat_v2 actigraphy 双路径跑通

### 目标

补齐 P1 的核心试验场:`feat_v2_biosensing`。该阶段用于回答"Spark 应该放在训练阶段,还是放在大规模特征/ETL 阶段"。

### OOM 判定与 pandas 路径改造

**结论**:原始 pandas 全量加载会 OOM,已改为逐 `id=*` 分区流式聚合。

证据:
- 全量 actigraphy 约 996 个分区,真实行数约 3.15 亿。
- 当前机器 RAM 约 31 GiB。
- 全量 `pd.read_parquet(series_root)` 展开后约 36 GB,其中 `id` object 字符串列约 20 GB,还不含 groupby/quantile 中间态。
- 改造后 pandas 每次只读取一个参与者分区和 9 个必要列,峰值 RSS 约 0.63 GB。

产物:
- 代码:`src/data/preprocess_actigraphy_pandas.py`
- 输出:`data/processed/feat_v2__cpu__seed42.parquet`
- shape:`3960 x 147`
- actigraphy 覆盖:`996/3960` 行
- 聚合耗时:约 39.45s

### Spark 路径尝试与最终方案

第一版尝试使用 Spark 原生 exact `percentile` 聚合,但失败:
- `percentile` 是 TypedImperativeAggregate,会为每组缓存/装箱大量 double。
- 在约 3.15 亿行 x 18 个分位数聚合下,即使 driver heap 提升到 12g,仍出现 GC overhead/OOM。
- `percentile_approx` 可以缓解内存,但不能满足方案要求的 `<1e-6` 精确等价性。

最终方案:
- 使用 `groupBy(id).applyInPandas(...)`。
- Spark 负责按参与者分片调度,每组调用同一份 pandas reducer。
- 这样保留精确分位数、NaN 处理、`std(ddof=1)` 等行为,同时把内存限制在单个参与者分区量级。

产物:
- 代码:`src/data/preprocess_actigraphy_spark.py`
- 输出:`data/processed/feat_v2__spark__seed42.parquet`
- shape:`3960 x 147`
- Spark master:`local[8]`
- 聚合耗时:约 120.91s

相关配置:
- `src/config.py`:Spark driver/executor memory 从 8g 调到 12g。
- `src/utils/spark.py`:新增 `pin_driver_memory()`,通过 `PYSPARK_SUBMIT_ARGS` 让 local/client 模式的 driver heap 在 JVM 启动前生效。

### 等价性校验

CPU/Spark 产物已通过列级等价性校验:

| 项 | 结果 |
|---|---|
| shape | CPU/Spark 均为 `3960 x 147` |
| actigraphy 列数 | 47 |
| actigraphy 覆盖 | CPU/Spark 均为 996 行 |
| id 集合 | 一致 |
| NaN 位置 | 一致 |
| 非 NaN 单元最大绝对差 | `1.14e-13` |
| 方案阈值 | `<1e-6` |

说明:raw parquet 文件 MD5 不应作为数值等价性依据,因为不同 backend/writer 的编码可能不同。Table 1 应使用排序后的逻辑 hash + NaN 感知 diff。

### 当前未完成项

- Table 1 已固化为 `reports/p1_feature_stage_feat_v2.csv`,并通过本地 SQLite fallback 写入 MLflow runs `feature_stage_pandas/spark`。
- Table 2 的 feat_v2 模型 6 行还未跑;`run_p1_systemwise.py` 仍硬编码 feat_v1。
- feat_v2 模型对比策略已定:主表使用全 3960 行 + 原 5-fold + 训练折内填补;996 actigraphy 子集作为 A5/补充分析单独做。
- `00_docs/PROGRESS.md` 已更新为当前快照。

### Table 1 固化(同日追加)

新增 `src/experiments/run_p1_feature_stage.py`,生成方案 §7.2 的 Table 1:

| backend | tool | wall(s) | peak RSS(GB) | logical hash | consistency |
|---|---|---:|---:|---|---|
| pandas | pandas_streaming | 38.13 | 0.65 | `5530ecc5f44fda5247629879523c3d38` | reference |
| spark | spark_applyInPandas, `local[8]` | 114.01 | 13.25 | `5530ecc5f44fda5247629879523c3d38` | `max_abs_diff=1.137e-13`;NaN equal |

工程补充:
- RSS 采用进程树采样,因此 Spark JVM 计入峰值内存。
- raw parquet MD5 仍保留在 CSV 中,但一致性判断使用 rounded logical hash + NaN 感知 diff。
- `.gitignore` 增加 `/reports/*.csv` 例外,使小型报告 CSV 可作为交付物入库。
- `scripts/start_mlflow.sh` 从旧的 `mlsys_cpu` 环境改为实际使用的 `openpi_311`。
- 在 sandbox 内 HTTP MLflow server 未运行,脚本 fallback 到 `sqlite:///mlruns.db` 并成功写入 `feature_stage_pandas` / `feature_stage_spark`。

### Table 2 主表补齐(同日追加)

扩展 `src/experiments/run_p1_systemwise.py`:
- 新增 `--feature v1|v2`。
- 新增 `--cohort all|actigraphy`。
- 新增 `load_feat_v2()` 读取 canonical `feat_v2__cpu__seed42.parquet`。
- 输出统一 schema 的报告 CSV,并记录 `feat_version` / `cohort` / `n_samples` / `n_features` 到 MLflow。

产物:
- `reports/p1_systemwise_feat_v1.csv` — v1/all 6 行(用新 schema 重跑)。
- `reports/p1_systemwise_feat_v2.csv` — v2/all 6 行。
- `reports/p1_systemwise_table2.csv` — Table 2 主表 12 行(v1+v2)。
- `reports/p1_systemwise_feat_v2_actigraphy.csv` — v2/actigraphy 子集 6 行,供 A5/覆盖率分析。
- `mlruns.db` — 已写入 `feat_v1_all_*`、`feat_v2_all_*`、`feat_v2_actigraphy_*` systemwise runs。

Table 2 主表要点:
- v2 全体样本没有带来明显指标提升:sklearn LR Macro-F1 `0.362 -> 0.359`,QWK `0.365 -> 0.343`;PyTorch MLP Macro-F1 约持平(`0.343 -> 0.341`)。
- Spark 训练阶段仍慢:Spark LR v2 约 `25.3s/fold`,单行推理约 `156 ms`,继续支撑"训练阶段 Spark 不适合本任务"。
- v2 actigraphy 子集共 996 个标注样本;第 4 折验证集没有 class 3,出现 sklearn metric warning,因此子集结果只作补充/A5,不替代主表。

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

> 注:上表为 2026-05-29 配置当时的快照;numpy/pandas 后续已降级到项目要求档位(**实测 numpy 1.26.4 / pandas 2.3.3**)。当前准确版本以 [`../envs/README.md`](../envs/README.md) 版本表为准。

---

### Kaggle API 配置

#### 踩坑: Kaggle 新版 API Token 方式

**问题**: Kaggle 现在使用 API Token 而不是 `kaggle.json` 文件。

**解决方案**:
1. 访问 https://www.kaggle.com/settings
2. 点击 "Create New Token"
3. 复制显示的 Token: `<redacted>`
4. 设置环境变量:

```bash
# 添加到 ~/.bashrc
echo 'export KAGGLE_API_TOKEN="<redacted>"' >> ~/.bashrc
source ~/.bashrc
```

**验证**:
```bash
conda activate openpi_311
export KAGGLE_API_TOKEN="<redacted>"
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
export KAGGLE_API_TOKEN="<redacted>"
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
- **2026-05-29 13:41**: 数据下载完成 (6.3 GB),解压成功
- **2026-05-29 14:02**: 数据加载测试通过;发现并处理两个关键数据特性 (见下方"关键数据发现")
- **2026-05-29 14:35**: W2 切分协议 — 生成 `stratified_group_kfold_seed42.csv` (2736 有标签样本, 5 折, 分层均衡, 无泄漏)
- **2026-05-29 14:38**: W2 feat_v1_tabular — 生成 `feat_v1__seed42.parquet` (3960×100, 58→98 编码特征, 数值列 NaN 留待按折填补)
- **2026-05-29 14:42**: W2 端到端打通 — sklearn LR 在 fold 0 跑出首个 baseline:**Macro-F1=0.368 / QWK=0.376 / BalAcc=0.420**。QWK 远离 1.0 佐证 PCIAT 泄漏已正确排除
- **2026-05-29 18:13**: W2 Spark 接入 — 修复 Java 21 / Python 3.12 两处环境不兼容(`src/utils/spark.py` 自动锁定 Java 8 + conda python);Spark LR fold0 ≈ sklearn,验证通过
- **2026-05-29 18:19**: W2 三系统对比表 1 完成 — sklearn/Spark/PyTorch × LR/MLP × 5-fold 全跑通(0 报错),结果写 `reports/p1_systemwise_feat_v1.csv` 并记入 MLflow。Spark 训练慢 30–100×、推理慢 ~1000×,印证"训练阶段 Spark 必输"

---

## 关键数据发现 (2026-05-29)

> ⚠️ 这是项目最重要的两条数据特性,直接决定建模正确性。任何特征工程都必须遵守。

### 发现 1: `sii` 标签存在大量缺失 (~31%)

数据探查结果 (train.csv, 3960 样本):

| sii | 含义 | 样本数 |
|---|---|---|
| 0.0 | None | 1594 |
| 1.0 | Mild | 730 |
| 2.0 | Moderate | 378 |
| 3.0 | Severe | 34 |
| NaN | 无标签 | 1224 (30.9%) |

**影响**:
- 有效标签样本仅 2736 个
- 类别极度不平衡 (sii=3 仅 34 个,占 0.86%)
- 这与 v2 文档 O13 的预期一致 (标签/actigraphy 缺失)

**处理**:
- `validate_data_integrity()` 已放宽:NaN 标签合法,只校验非 NaN 值 ∈ {0,1,2,3}
- 后续建模需决定:监督训练只用有标签样本;无标签样本可用于半监督/伪标签 (可选加强)
- 评估指标 QWK + class_weight='balanced' 应对不平衡

### 发现 2: PCIAT-* 列是标签泄漏源 (致命陷阱) 🚨

**验证结果** (sii 与 PCIAT-PCIAT_Total 的对应关系):

| sii | PCIAT_Total 范围 | 样本数 |
|---|---|---|
| 0 | [0, 30] | 1594 |
| 1 | [31, 49] | 730 |
| 2 | [50, 79] | 378 |
| 3 | [80, 93] | 34 |

`sii` 标签**完全由 `PCIAT-PCIAT_Total` 分箱得到** (官方阈值 0/31/50/80)。这意味着:

- 全部 22 个 `PCIAT-*` 列 (Season + 20 个分项 + Total) 都是答案的完美编码
- 若把它们当特征,模型会"用答案预测答案",训练集近乎满分,**真实测试集完全失效**
- 这是该 Kaggle 竞赛参赛者最常踩的坑

**处理** (已落地到代码):
- `src/data/constants.py` 新增 `LEAKAGE_COL_PREFIXES = ["PCIAT"]` 与 `SII_BIN_EDGES`
- `src/data/loader.py` 新增:
  - `get_leakage_columns(df)` — 识别泄漏列
  - `get_feature_columns(df, is_train)` — 返回干净特征列 (自动排除 id/sii/PCIAT-*)
- 实测:82 列 → 排除 22 泄漏列 + id + sii → **58 个可用特征**

**铁律**: 所有特征工程、所有模型,一律通过 `get_feature_columns()` 取特征,严禁手工 include PCIAT 列。

---

## W2 Spark 接入:两个兼容性坑 + 三系统对比表 1 (2026-05-29)

### 踩坑:Spark 3.5 连环兼容性问题

接入 Spark MLlib baseline 时,连续撞到两个**环境层**不兼容(都与模型无关):

1. **Java 版本** 🚨:系统默认 `java` 是 OpenJDK **21**,而 Spark 3.5 只支持 Java **8/11/17**(Java 21 要 Spark 4.0)。表现为 SparkSession 启动即崩。
   - 修复:`src/utils/spark.py::pin_java_home()` 自动探测并把 `JAVA_HOME` 指向兼容 JDK(本机已装 Java 8 `1.8.0_492`,无需安装;可用 `MLSYS_JAVA_HOME` 覆盖为 17)。
2. **Python 版本** 🚨:Spark worker 默认用系统 `python3`(Ubuntu 24.04 = **3.12**),而 driver 是 conda `openpi_311` = **3.11**,每个 job 报 `PYTHON_VERSION_MISMATCH`。
   - 修复:`pin_worker_python()` 把 `PYSPARK_PYTHON`/`PYSPARK_DRIVER_PYTHON` 锁到 `sys.executable`。

两处都在 `src/utils/spark.py` import 时自动生效,**无需在 shell 里 export 任何东西**。所有 Spark 代码统一走 `get_spark_session()`(单例,JVM 只启一次,跨 fold/模型复用)。

### 新增文件
- `src/utils/spark.py` — Java/Python 双锁定 + 缓存 SparkSession
- `src/models/spark_baselines.py` — `SparkLogisticRegression`(多分类 + balanced weightCol)/ `SparkMLP`(MLlib MLP,无 class weight,系统差异)
- `src/experiments/run_p1_systemwise.py` — 三系统统一跑 `run_cv`,输出对比表 1 + 写 `reports/p1_systemwise_feat_v1.csv` + 记 MLflow
- `src/training/cv.py` — `run_cv` 新增 `latency_warmup/latency_iters`(Spark 单行 predict 是整个 job,200 次会拖垮)

### 对比表 1(feat_v1,5-fold 均值;6 个配置 0 报错,已记入 MLflow `piu-p1-systemwise`)

| system  | algo | Macro-F1 | QWK   | BalAcc | train(s) | infer(µs) |
|---------|------|----------|-------|--------|----------|-----------|
| sklearn | LR   | 0.362    | 0.365 | 0.404  | 8.6      | 45        |
| sklearn | MLP  | 0.303    | 0.285 | 0.309  | 0.2      | 125       |
| spark   | LR   | 0.362    | 0.360 | 0.399  | 22.6     | 145,000   |
| spark   | MLP  | 0.300    | 0.249 | 0.300  | 4.3      | 135,000   |
| pytorch | LR   | 0.347    | 0.335 | 0.419  | 0.7      | 58        |
| pytorch | MLP  | 0.343    | 0.348 | 0.439  | 0.1      | 82        |

**关键结论(正中方案论点)**:
- **质量**:spark_lr ≈ sklearn_lr(Macro-F1 0.362 几乎完全一致)→ 证明跨系统对比公平、实现正确。
- **训练耗时**:Spark 比 sklearn/pytorch 慢 **30–100×**(2736 行小数据,Spark 启动/调度开销远大于收益)。
- **推理延迟**:Spark 单行 ~**135–145 ms**,比 sklearn/pytorch 慢 **~1000–3000×**(每次 predict 都是一个完整 Spark job)。
- → 印证 `03_plan_p1_v2` 核心论点:**训练阶段 Spark 必输给单机;Spark 的价值在特征/ETL 阶段(feat_v2 actigraphy)**,正是下一步。

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

**最后更新**: 2026-05-29 18:19
**当前阶段**: W2 — 三系统(sklearn/Spark/PyTorch)feat_v1 对比表 1 已完成;Spark 环境打通
**下一步**: feat_v2 actigraphy 滑窗统计(pandas 版 + Spark 版两路对比)— Spark 的核心价值试验场

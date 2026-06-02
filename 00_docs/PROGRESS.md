# 项目进展快照(PROGRESS)

> **本文件定位**:随时覆盖更新的「现在在哪 / 下一步去哪」状态快照。
> 时间线流水日志见 [`PROJECT_LOG.md`](./PROJECT_LOG.md);方案与实验设计见 [`v2/03_plan_p1_v2.md`](./v2/03_plan_p1_v2.md)。
>
> **更新时间**:2026-06-03 · **当前阶段**:W3 消融与可视化
> **一句话**:P1 多系统算法对比主表已完成;W3 已完成 A5/A6 和核心可视化,下一步推进 A1-A4 或整理中期材料。

---

## 1. 当前状态总览

| 模块 | 状态 | 产物 / 证据 |
|---|---|---|
| 环境 `openpi_311` | 已完成 | `envs/pinned_openpi_311_mlsys.txt`;PyTorch 2.9+cu128 支持 sm_120 |
| PIU 数据 | 已完成 | `data/raw/`;996 个 actigraphy 分区,真实总行数约 3.15 亿 |
| 切分协议 | 已完成 | `data/splits/stratified_group_kfold_seed42.csv` |
| 两条数据铁律 | 已完成 | 标签缺失约 31%;`PCIAT-*` 泄漏列已排除 |
| `feat_v1_tabular` | 已完成 | `data/processed/feat_v1__seed42.parquet`(3960 x 100) |
| 三系统 x 两算法 x feat_v1 | 已完成 | `reports/p1_systemwise_feat_v1.csv`;MLflow `piu-p1-systemwise` |
| `feat_v2` 特征规格 | 已完成 | `src/data/actigraphy_features.py` 定义 47 个 `act_*` 列 |
| `feat_v2` pandas 路径 | 已完成 | `data/processed/feat_v2__cpu__seed42.parquet`(3960 x 147);流式分区聚合避免 OOM |
| `feat_v2` Spark 路径 | 已完成 | `data/processed/feat_v2__spark__seed42.parquet`(3960 x 147);`applyInPandas`, `local[8]` |
| CPU/Spark 等价性 | 已通过 | NaN 位置一致;非 NaN 单元 `max_abs_diff=1.14e-13 < 1e-6` |
| Table 1:特征阶段对比 | 已完成 | `reports/p1_feature_stage_feat_v2.csv`;MLflow runs `feature_stage_pandas/spark` |
| Table 2:模型阶段 12 行 | 已完成 | `reports/p1_systemwise_table2.csv`;v1/v2 各 6 行;MLflow systemwise runs 已补齐 |
| feat_v2 actigraphy 子集 | 已完成(补充) | `reports/p1_systemwise_feat_v2_actigraphy.csv`;996 样本,作为 A5/覆盖率分析素材 |
| W3 A5 actigraphy 覆盖率分析 | 已完成 | `reports/p1_ablation_a5_coverage.csv`;`reports/p1_ablation_a5_fold_coverage.csv` |
| W3 A6 Spark 并行度扫描 | 已完成 | `reports/p1_spark_parallelism_feat_v2.csv`;`local[4]/[8]/[20]` 均等价,但并行度越高越慢且更耗内存 |
| W3 核心可视化 | 已完成 | `reports/figures/`;Table 2 指标、系统开销、A5 覆盖率、A6 并行度、代表性混淆矩阵、lineage |
| W3 其余消融 | 待开始 | A1-A4;`feat_v3_fusion` 可选 |

---

## 2. 已完成成果

### 2.1 feat_v1 模型对比(5-fold 均值)

来源:`reports/p1_systemwise_feat_v1.csv`,6 个配置 0 报错。

| system | algo | Macro-F1 | QWK | BalAcc | train(s) | infer(us) |
|---|---|---:|---:|---:|---:|---:|
| sklearn | LR | 0.362 | 0.365 | 0.404 | 9.0 | 38 |
| sklearn | MLP | 0.303 | 0.285 | 0.309 | 0.3 | 149 |
| spark | LR | 0.363 | 0.361 | 0.399 | 24.2 | 161425 |
| spark | MLP | 0.301 | 0.248 | 0.302 | 4.5 | 150003 |
| pytorch | LR | 0.347 | 0.335 | 0.419 | 0.6 | 71 |
| pytorch | MLP | 0.343 | 0.348 | 0.439 | 0.1 | 119 |

结论:Spark LR 与 sklearn LR 指标接近,说明跨系统实现基本公平;但小表格训练与单行推理阶段 Spark 调度开销极大,支撑「Spark 价值应放在特征/ETL 阶段」的核心论点。

### 2.2 feat_v2 actigraphy 双路径

| 路径 | 状态 | 关键指标 |
|---|---|---|
| pandas streaming | 已跑通 | 逐 `id=*` 分区读取;Table 1 实测 38.13s / 0.65 GB 进程树 RSS |
| Spark applyInPandas | 已跑通 | `local[8]`;Table 1 实测 114.01s / 13.25 GB 进程树 RSS |
| 等价性 | 已通过 | 47 个 `act_*` 列;996/3960 行有 actigraphy;非 NaN `max_abs_diff=1.14e-13` |

关键发现:
- 原始 pandas 全量 `pd.read_parquet(series_root)` 会 OOM:全量展开约 36 GB,超过 31 GiB RAM,且不含 groupby 中间态。
- Spark 原生 exact `percentile` 在此规模下不可用:它会为每组缓存/装箱大量 double,12g driver heap 仍触发 GC overhead/OOM。
- 当前 Spark 版采用 `groupBy(id).applyInPandas(...)`,让 Spark 负责分片调度,由同一份 pandas reducer 做精确聚合。
- 本机 local[8] 下 Spark 特征阶段仍约 3.0x 慢于 pandas streaming,但 Table 1 已能清楚展示"训练阶段 Spark 更差,特征阶段也需看数据形态/算法实现"这一更细的结论。

### 2.3 Table 1 特征阶段对比

来源:`reports/p1_feature_stage_feat_v2.csv`,由 `python -m src.experiments.run_p1_feature_stage --mlflow` 生成。

| backend | tool | wall(s) | peak RSS(GB) | rows x cols | act rows | logical hash | consistency |
|---|---|---:|---:|---|---:|---|---|
| pandas | pandas_streaming | 38.13 | 0.65 | 3960 x 147 | 996 | `5530ecc5...` | reference |
| spark | spark_applyInPandas local[8] | 114.01 | 13.25 | 3960 x 147 | 996 | `5530ecc5...` | `max_abs_diff=1.14e-13`, NaN equal |

MLflow:HTTP server 未运行时脚本 fallback 到本地 `sqlite:///mlruns.db`,已写入 `feature_stage_pandas` 与 `feature_stage_spark` 两个 FINISHED run。`scripts/start_mlflow.sh` 已改为激活实际环境 `openpi_311`。

### 2.4 Table 2 模型阶段主表(12 行)

来源:`reports/p1_systemwise_table2.csv`,由 `run_p1_systemwise.py --feature v1/v2 --mlflow` 生成。`feat_v2` 主表使用全 3960 行、原 5-fold;无 actigraphy 的行由训练折内 imputer 处理。

| feature | system | algo | Macro-F1 | QWK | BalAcc | train(s) | infer(us) |
|---|---|---|---:|---:|---:|---:|---:|
| v1 | sklearn | LR | 0.362 | 0.365 | 0.404 | 9.0 | 38 |
| v1 | spark | LR | 0.363 | 0.361 | 0.399 | 24.2 | 161425 |
| v1 | pytorch | LR | 0.347 | 0.335 | 0.419 | 0.6 | 71 |
| v1 | sklearn | MLP | 0.303 | 0.285 | 0.309 | 0.3 | 149 |
| v1 | spark | MLP | 0.301 | 0.248 | 0.302 | 4.5 | 150003 |
| v1 | pytorch | MLP | 0.343 | 0.348 | 0.439 | 0.1 | 119 |
| v2 | sklearn | LR | 0.359 | 0.343 | 0.405 | 6.8 | 43 |
| v2 | spark | LR | 0.344 | 0.342 | 0.367 | 25.3 | 156464 |
| v2 | pytorch | LR | 0.344 | 0.338 | 0.399 | 0.6 | 72 |
| v2 | sklearn | MLP | 0.308 | 0.280 | 0.314 | 0.4 | 223 |
| v2 | spark | MLP | 0.335 | 0.265 | 0.334 | 4.2 | 154740 |
| v2 | pytorch | MLP | 0.341 | 0.333 | 0.426 | 0.1 | 112 |

主结论:
- `feat_v2` 全体样本没有显著提升主指标;LR 反而略降,说明 996/3960 的 actigraphy 覆盖被全体填补稀释。
- Spark 在训练阶段仍然慢,单行推理仍约 150-160 ms/job;即使特征维度增加到 v2,训练阶段不构成 Spark 优势。
- `feat_v2 actigraphy` 子集表已生成(`reports/p1_systemwise_feat_v2_actigraphy.csv`),但仅作补充/A5:第 4 折验证集无 class 3,出现 `y_pred contains classes not in y_true` 警告,不可直接替代主表。

### 2.5 W3 A6 Spark 并行度扫描

来源:`reports/p1_spark_parallelism_feat_v2.csv`,由 `python -m src.experiments.run_p1_spark_parallelism --masters local[4],local[8],local[20] --mlflow` 生成。

| Spark master | wall(s) | peak RSS(GB) | logical hash | 等价性 |
|---|---:|---:|---|---|
| `local[4]` | 115.48 | 12.42 | `5530ecc5...` | `max_abs_diff=5.68e-14`,NaN equal |
| `local[8]` | 138.12 | 13.29 | `5530ecc5...` | `max_abs_diff=1.14e-13`,NaN equal |
| `local[20]` | 161.53 | 18.00 | `5530ecc5...` | `max_abs_diff=1.14e-13`,NaN equal |

结论:
- 三个并行度产物均与 pandas reference 等价,说明 A6 比较的是系统调度/资源曲线,不是算法误差。
- 本机最佳点是 `local[4]`;继续增加 local cores 没有提速,反而 `local[20]` 比 `local[4]` 慢约 40%,峰值 RSS 多约 5.6 GB。
- 对当前 `groupBy(id).applyInPandas` 精确聚合路径而言,瓶颈更像 shuffle/序列化/I/O 与每组 pandas reducer 的尾部任务,而不是 CPU core 数不足。

### 2.6 W3 A5 actigraphy 覆盖率分析

来源:`reports/p1_ablation_a5_coverage.csv` 与 `reports/p1_ablation_a5_fold_coverage.csv`,由 `python -m src.experiments.run_p1_ablation_a5_coverage` 生成。

覆盖率事实:

| 口径 | 覆盖数 | 覆盖率 |
|---|---:|---:|
| 全体 feature 行 | 996 / 3960 | 25.2% |
| 有标签 CV 样本 | 996 / 2736 | 36.4% |

actigraphy 子集 5-fold 风险:

| fold | all n | actigraphy n | coverage | actigraphy class 3 |
|---:|---:|---:|---:|---:|
| 0 | 547 | 200 | 36.6% | 3 |
| 1 | 548 | 215 | 39.2% | 4 |
| 2 | 547 | 200 | 36.6% | 1 |
| 3 | 547 | 192 | 35.1% | 2 |
| 4 | 547 | 189 | 34.6% | 0 |

主结论:
- `v2/all` 与 `v1/all` 是同 2736 标注样本 + 原 5-fold 的公平主协议;该协议下 `feat_v2` 没有稳定提升。LR 三系统 Macro-F1 均略降(`sklearn -0.003`,`spark -0.019`,`pytorch -0.002`);MLP 只有 Spark MLP 明显上升(`+0.033`),不构成跨系统稳定收益。
- `v2/actigraphy` 子集只回答"有真实 actigraphy 的人群上表现如何",不能替代主表:样本数降到 996,且 fold 4 没有 class 3 验证样本。
- 因此对论文/汇报的表述应是:actigraphy 特征工程已可复现且与 Spark 等价,但当前覆盖率与类别稀疏使其没有转化成稳定主表收益;子集结果作为覆盖率敏感性分析而不是主结论。

### 2.7 W3 核心可视化

来源:`python -m src.experiments.run_p1_visualizations`,输出到 `reports/figures/`,每张图同时保存 `.svg` 和 `.png`。

| 图 | 用途 |
|---|---|
| `p1_table2_metric_bars` | Table 2 的 Macro-F1 / QWK / Balanced Accuracy 跨系统对比 |
| `p1_system_costs` | `feat_v2/all` 训练耗时与单行推理延迟,突出 Spark 训练/推理开销 |
| `p1_a6_spark_parallelism` | A6 `local[4]/[8]/[20]` wall time 与 RSS 曲线 |
| `p1_a5_coverage` | A5 fold 覆盖率与 actigraphy 子集 class 分布 |
| `p1_confusion_sklearn_lr` | 代表性 `sklearn LR` v1/all vs v2/all out-of-fold 混淆矩阵 |
| `p1_feature_lineage` | pandas streaming 与 Spark applyInPandas 的 feat_v2 特征 lineage |

验证:
- 12 个图像文件(6 张 x SVG/PNG)均已生成。
- PNG 像素非空检查通过。
- 抽查 `p1_table2_metric_bars`、`p1_a5_coverage`、`p1_a6_spark_parallelism`、`p1_confusion_sklearn_lr`、`p1_feature_lineage` 无明显遮挡或裁切。

---

## 3. 当前待办

1. **W3 消融与可视化**
   - A1-A4 消融;A5 覆盖率分析、A6 并行度扫描与核心可视化已完成。
   - `feat_v3_fusion` 可选,不阻塞 P1 主结论。
   - 下一步建议整理中期材料/报告骨架,或选择性补 A1-A4 轻量消融。

---

## 4. 开机备忘

```bash
source /home/er/Devenv/Anaconda3/etc/profile.d/conda.sh
conda activate openpi_311
curl -s http://localhost:5000/health || bash scripts/start_mlflow.sh
git status -s
```

下一步推荐命令:

```bash
python -m src.experiments.run_p1_feature_stage --mlflow
python -m src.experiments.run_p1_ablation_a5_coverage
python -m src.experiments.run_p1_spark_parallelism --mlflow
python -m src.experiments.run_p1_visualizations
python -m src.experiments.run_p1_systemwise --feature v2 --mlflow
python -m src.experiments.run_p1_systemwise --feature v2 --cohort actigraphy --mlflow
```

上述脚本均已实现并跑通。

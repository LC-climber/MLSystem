# 项目进展快照(PROGRESS)

> **本文件定位**:随时覆盖更新的「现在在哪 / 下一步去哪」状态快照。
> 时间线流水日志见 [`PROJECT_LOG.md`](./PROJECT_LOG.md);方案与实验设计见 [`v2/03_plan_p1_v2.md`](./v2/03_plan_p1_v2.md)。
>
> **更新时间**:2026-06-02 · **当前阶段**:W2 收口 -> W3
> **一句话**:feat_v2 actigraphy 双路径与 Table 1 特征阶段对比均已固化;下一步是扩展模型对比脚本并补 Table 2 的 feat_v2 模型 6 行。

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
| Table 2:feat_v2 模型 6 行 | 待开始 | `run_p1_systemwise.py` 仍只支持 feat_v1 |
| W3 消融与可视化 | 待开始 | A1-A6、雷达图、混淆矩阵、Spark 并行度曲线 |

---

## 2. 已完成成果

### 2.1 feat_v1 模型对比(5-fold 均值)

来源:`reports/p1_systemwise_feat_v1.csv`,6 个配置 0 报错。

| system | algo | Macro-F1 | QWK | BalAcc | train(s) | infer(us) |
|---|---|---:|---:|---:|---:|---:|
| sklearn | LR | 0.362 | 0.365 | 0.404 | 8.6 | 45 |
| sklearn | MLP | 0.303 | 0.285 | 0.309 | 0.2 | 125 |
| spark | LR | 0.362 | 0.360 | 0.399 | 22.6 | 145025 |
| spark | MLP | 0.300 | 0.249 | 0.300 | 4.3 | 134902 |
| pytorch | LR | 0.347 | 0.335 | 0.419 | 0.7 | 58 |
| pytorch | MLP | 0.343 | 0.348 | 0.439 | 0.1 | 82 |

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

---

## 3. 当前待办

1. **扩展 Table 2 到 feat_v2**
   - 给 `run_p1_systemwise.py` 增加 `--feature v1|v2`。
   - 增加 `load_feat_v2` 或等价加载入口。
   - 主表使用全 3960 行 + 原 5-fold + 训练折内填补,保持与 feat_v1 可比。
   - 996 actigraphy 子集也做,作为 A5/补充分析;该子集需要单独处理 fold 与样本量解释。

2. **W3 后续**
   - A1-A6 消融,尤其 A6 Spark `local[4]/[8]/[20]` 并行度扫描。
   - 跨系统雷达图、混淆矩阵、pandas vs Spark lineage/流程图。
   - `feat_v3_fusion` 可选,不阻塞 P1 主结论。

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
python -m src.experiments.run_p1_systemwise --feature v2 --mlflow
```

`run_p1_feature_stage` 已实现并跑通;`run_p1_systemwise --feature v2` 仍需实现。

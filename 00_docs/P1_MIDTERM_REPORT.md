# P1 中期汇报文档:PIU 多系统算法对比

> 更新时间:2026-06-03  
> 对应代码与产物:Table 1 / Table 2 / A5 / A6 / W3 可视化已全部落地。  
> 汇报定位:解释"Spark 到底该放在 ML 流水线的哪里",并给出可复现实验结果。

---

## 1. 一句话结论

在 PIU 这个任务上,Spark 不适合放在小表格模型训练/单样本推理阶段;它的合理位置应是大规模特征/ETL 阶段。但即使在 3.15 亿行 actigraphy 特征阶段,Spark 也不是"并行度越高越快":精确分位数与 per-participant 聚合需要算法实现配合,本机实测 `local[4]` 反而快于 `local[8]/local[20]`。

---

## 2. 问题与实验设计

### 2.1 任务

- 数据集:Child Mind Institute Problematic Internet Use(PIU)
- 预测目标:`sii` 四分类,类别为 0/1/2/3
- P1 主目标:比较同一任务在 sklearn / Spark MLlib / PyTorch 三个系统中的模型质量与系统成本
- 主指标:Macro-F1
- 辅指标:QWK、Balanced Accuracy、训练耗时、推理延迟、RSS、模型大小

### 2.2 特征版本

| 特征版本 | 内容 | 状态 |
|---|---|---|
| `feat_v1_tabular` | 表格特征 + one-hot season;缺失填补/标准化在 fold 内做 | 已完成 |
| `feat_v2_biosensing` | `feat_v1` + 47 个 actigraphy 聚合特征 | 已完成 |

### 2.3 公平协议

- 固定 `seed=42`
- 5-fold stratified group split
- 所有系统使用同样 feature、fold、预处理策略
- imputer/scaler 只在训练 fold fit,避免泄漏
- 泄漏列 `PCIAT-*` 已排除
- `feat_v2` 主表保留全 3960 行,无 actigraphy 的样本由训练 fold imputer 处理

---

## 3. 数据关键事实

| 项 | 数值 | 影响 |
|---|---:|---|
| 全体 train 行 | 3960 | feature 文件总行数 |
| 有标签 CV 样本 | 2736 | Table 2 实际训练/验证样本 |
| actigraphy 分区 | 996 | 有原始时序的人数 |
| actigraphy 原始行数 | 约 3.15 亿 | 特征阶段有真实大数据量 |
| 全体 actigraphy 覆盖 | 996 / 3960 = 25.2% | `feat_v2/all` 大量 act 列缺失 |
| 有标签 actigraphy 覆盖 | 996 / 2736 = 36.4% | 主表 v2 效果被覆盖率限制 |
| actigraphy 子集 fold 4 class 3 | 0 | 子集表只能作补充,不能替代主表 |

---

## 4. Table 1:特征阶段 pandas vs Spark

来源:`reports/p1_feature_stage_feat_v2.csv`

| backend | 方法 | wall(s) | peak RSS(GB) | 等价性 |
|---|---|---:|---:|---|
| pandas | streaming by `id=*` | 38.13 | 0.65 | reference |
| Spark | `groupBy(id).applyInPandas` | 114.01 | 13.25 | `max_abs_diff=1.14e-13` |

结论:
- 原始 pandas 全量读取会 OOM;改为按 participant 流式聚合后,单机 pandas 很稳。
- Spark 原生 exact `percentile` 会触发 GC/OOM;最终 Spark 路径改为 `applyInPandas`,复用同一份 reducer 保证等价。
- 本机 local mode 下 Spark 特征阶段仍慢于 pandas,说明"Spark 属于 ETL 阶段"不等于"任何 Spark 实现都会赢"。

---

## 5. Table 2:三系统 x 两算法 x 两特征版本

来源:`reports/p1_systemwise_table2.csv`

### 5.1 主表摘要

| feature | system | algo | Macro-F1 | QWK | train(s) | infer(us) |
|---|---|---|---:|---:|---:|---:|
| v1 | sklearn | LR | 0.362 | 0.365 | 9.0 | 38 |
| v1 | spark | LR | 0.363 | 0.361 | 24.2 | 161425 |
| v1 | pytorch | LR | 0.347 | 0.335 | 0.6 | 71 |
| v2 | sklearn | LR | 0.359 | 0.343 | 6.8 | 43 |
| v2 | spark | LR | 0.344 | 0.342 | 25.3 | 156464 |
| v2 | pytorch | LR | 0.344 | 0.338 | 0.6 | 72 |

MLP 结果:
- sklearn MLP:`v1 0.303 -> v2 0.308` Macro-F1,轻微提升
- Spark MLP:`v1 0.301 -> v2 0.335` Macro-F1,提升明显但 QWK 仍低
- PyTorch MLP:`v1 0.343 -> v2 0.341` Macro-F1,约持平

### 5.2 系统层结论

- 模型质量:Spark LR 与 sklearn LR 在 `feat_v1` 上接近,说明跨系统实现基本公平。
- 训练阶段:Spark 在小表格训练上没有优势。
- 推理阶段:Spark 单样本推理约 150-160 ms/job,远慢于 sklearn/PyTorch 的几十到几百微秒。
- 特征版本:`feat_v2/all` 没有稳定提升主指标,原因不是实现错误,而是 actigraphy 覆盖率不足且类别稀疏。

---

## 6. A5:actigraphy 覆盖率解释

来源:
- `reports/p1_ablation_a5_coverage.csv`
- `reports/p1_ablation_a5_fold_coverage.csv`

同协议主表(`v2/all - v1/all`)下:

| family | Macro-F1 delta |
|---|---|
| sklearn LR | -0.003 |
| Spark LR | -0.019 |
| PyTorch LR | -0.002 |
| sklearn MLP | +0.005 |
| Spark MLP | +0.033 |
| PyTorch MLP | -0.002 |

解释:
- LR 三系统均略降,说明 actigraphy 特征没有稳定提升线性模型。
- MLP 只有 Spark MLP 明显提升,但不是跨系统稳定收益。
- `v2/actigraphy` 子集只有 996 个有 actigraphy 的标注样本,fold 4 无 class 3,所以只能作为覆盖率敏感性分析。

---

## 7. A6:Spark 并行度扫描

来源:`reports/p1_spark_parallelism_feat_v2.csv`

| Spark master | wall(s) | peak RSS(GB) | 等价性 |
|---|---:|---:|---|
| `local[4]` | 115.48 | 12.42 | pass |
| `local[8]` | 138.12 | 13.29 | pass |
| `local[20]` | 161.53 | 18.00 | pass |

结论:
- 三个产物都与 pandas reference 等价。
- 并行度越高反而越慢、RSS 越高。
- 当前瓶颈更像 shuffle/序列化/Python worker 调度与尾部任务,不是 CPU core 数不足。

---

## 8. 可视化材料

来源:`reports/figures/`

| 图 | 汇报用途 |
|---|---|
| `p1_table2_metric_bars` | 说明 v2 没有稳定压过 v1 |
| `p1_system_costs` | 展示 Spark 训练/推理阶段系统开销 |
| `p1_a5_coverage` | 解释 actigraphy 覆盖率与 fold 4 class 3 缺失 |
| `p1_a6_spark_parallelism` | 展示并行度越高越慢的实测曲线 |
| `p1_confusion_sklearn_lr` | 展示类别 3 极少且易混淆 |
| `p1_feature_lineage` | 解释 pandas reference 与 Spark candidate 的特征血缘 |

---

## 9. 汇报讲稿建议(10-12 分钟)

1. **开场(1 min)**  
   我们不是只比较模型分数,而是比较三套 ML 系统在同一任务中的质量和系统成本。

2. **任务与协议(1.5 min)**  
   PIU 四分类,5-fold,三系统 x 两算法,主指标 Macro-F1,所有系统共享同一套 fold 和预处理。

3. **Spark 应该放哪里(2 min)**  
   小表格训练阶段 Spark 调度开销大;真正可能有价值的是 3.15 亿行 actigraphy 特征阶段。

4. **Table 1(1.5 min)**  
   pandas streaming 38s/0.65GB,Spark 114s/13.25GB,两者数值等价。结论:Spark 不是自动赢,实现方式很关键。

5. **Table 2(2 min)**  
   sklearn/Spark/PyTorch 模型质量接近,但 Spark 训练/推理成本显著高。`feat_v2` 主表没有稳定提升。

6. **A5 + A6(2 min)**  
   A5 解释 v2 为什么没有稳定收益:actigraphy 有标签覆盖率只有 36.4%,fold 4 class 3 为 0。A6 说明 Spark 并行度需要实测,`local[4]` 最优。

7. **结论与下一步(1 min)**  
   P1 核心结论成立;下一步进入 P2 MLOps,或补 A1-A4 轻量消融作为附录。

---

## 10. 交付物索引

| 类型 | 路径 |
|---|---|
| 报告文档 | `00_docs/P1_MIDTERM_REPORT.md` |
| PPT | `reports/p1_midterm_slides.pptx` |
| 动画 HTML | `reports/p1_midterm_explainer.html` |
| 可视化图 | `reports/figures/` |
| Table 1 | `reports/p1_feature_stage_feat_v2.csv` |
| Table 2 | `reports/p1_systemwise_table2.csv` |
| A5 | `reports/p1_ablation_a5_coverage.csv` |
| A6 | `reports/p1_spark_parallelism_feat_v2.csv` |

---

## 11. 风险与诚实边界

- `feat_v2/actigraphy` 子集不是主协议,不能直接替代 Table 2。
- Spark 特征阶段在本机 local mode 未胜过 pandas streaming,但该结果本身有价值:它说明 Spark 需要匹配正确算法与部署形态。
- 混淆矩阵目前只做代表性 `sklearn LR` v1/v2,用于解释类别混淆,不是全 12 行配置的混淆矩阵全集。
- `python-pptx` 是为生成 PPT 新增的依赖,已补入环境 pinned 文件。

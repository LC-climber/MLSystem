# P1 中期汇报答辩 Q&A 备忘

> 用途:老师追问时快速定位回答口径。  
> 原则:先给结论,再给证据,最后给边界。

---

## 1. 为什么 Spark 没有赢?

短答:
- 因为这个任务的模型训练阶段是小表格,不是 Spark 的优势场景。Spark 的 job 调度、DataFrame 转换和 JVM/Python 边界开销远大于实际计算量。

证据:
- Table 2 中 Spark 单行推理约 `150-160 ms/job`,sklearn/PyTorch 是微秒级。
- Spark LR 与 sklearn LR 的质量接近,说明不是模型实现完全错了,而是系统开销不适合这个阶段。

边界:
- 这不等于 Spark 没价值;只是说明 Spark 不应该用于这个任务的训练/单样本推理阶段。

---

## 2. 那为什么还说 Spark 的价值在 ETL?

短答:
- 因为 actigraphy 原始时序约 3.15 亿行,这是表格训练阶段完全不同的数据规模。Spark 的分布式数据处理能力应该在这里验证。

证据:
- `feat_v2` 特征阶段专门做了 pandas streaming vs Spark applyInPandas。
- Spark 产物与 pandas reference 等价,`max_abs_diff` 约 `1e-13`。

边界:
- 本机 local mode 下 Spark 仍慢于 pandas streaming,所以更准确的结论是:Spark 的合理位置在 ETL,但 ETL 也需要算法感知实现和真实并行环境。

---

## 3. 为什么 pandas 这么快?是不是比较不公平?

短答:
- pandas 快是因为我们写的是合理的 streaming baseline,不是 naive 全量读取。数据本身按 `id=*` 分区,每个 participant 天然可以单独聚合。

证据:
- naive pandas 全量读取会展开到约 36GB 并 OOM。
- streaming pandas 逐 participant 读取,峰值 RSS 约 0.65GB,38s 完成。

边界:
- 这是公平 baseline:如果数据分区结构天然适合单机流式处理,系统比较就应该承认这一点。

---

## 4. 为什么不用 Spark 原生 percentile?

短答:
- Spark 原生 exact `percentile` 对这个规模的 per-group 精确分位数聚合内存开销太大,会触发 GC/OOM。

证据:
- exact percentile 是 TypedImperativeAggregate,会缓存/装箱大量 double。
- 12GB driver heap 仍出现 GC overhead/OOM。
- `percentile_approx` 可以快,但不满足 `<1e-6` 精确等价要求。

最终方案:
- 使用 `groupBy(id).applyInPandas`,Spark 负责分片,同一份 pandas reducer 负责精确聚合。

---

## 5. feat_v2 为什么没有提升?

短答:
- 主要原因是 actigraphy 覆盖率不足和类别稀疏,不是特征工程无法复现。

证据:
- 全体 feature 行 actigraphy 覆盖率 `25.2%`。
- 有标签 CV 样本覆盖率 `36.4%`。
- fold 4 的 actigraphy 子集没有 class 3 验证样本。
- `v2/all - v1/all` 下 LR 三系统 Macro-F1 都略降。

边界:
- Spark MLP 在 Macro-F1 上有提升,但不是跨系统稳定收益,不能把它解读为 `feat_v2` 全局有效。

---

## 6. 为什么不用 actigraphy 子集作为主结论?

短答:
- 因为它改变了主协议:样本从 2736 降到 996,并且 fold 4 没有 class 3。这样得到的指标不能和 Table 2 主表直接公平比较。

证据:
- actigraphy 子集只保留有真实 actigraphy 的标注样本。
- class 3 本来就少,子集进一步稀疏。

推荐回答:
- 我们把它作为 A5 覆盖率敏感性分析,用于解释主表,不替代主表。

---

## 7. A6 为什么并行度越高越慢?

短答:
- 当前 Spark 路径瓶颈不是单纯 CPU core 数,而是 shuffle、序列化、Python worker 调度和尾部任务。提高 local cores 会增加并发内存和调度压力。

证据:
- `local[4]`:115.48s / 12.42GB
- `local[8]`:138.12s / 13.29GB
- `local[20]`:161.53s / 18.00GB
- 三者都与 pandas reference 等价。

结论:
- Spark 并行度需要实测拐点,不是越高越好。

---

## 8. 三个系统的实现公平吗?

短答:
- 已尽量控制公平变量:同一 feature、同一 fold、同一 seed、同一预处理协议。

证据:
- Spark LR 与 sklearn LR 在 `feat_v1` 上指标接近,说明 LR 实现基本可比。
- 训练 fold 内 fit imputer/scaler,避免预处理泄漏。

边界:
- MLP 不同系统底层实现并不完全相同,例如 sklearn MLP 不支持 class_weight。这在文档中作为系统差异记录。

---

## 9. 为什么主指标用 Macro-F1?

短答:
- 任务类别不均衡,class 3 很少。Macro-F1 能让尾类错误对指标有影响,适合 P1 的多系统公平比较。

补充:
- 同时报告 QWK 和 Balanced Accuracy,避免只看单一指标。

---

## 10. 混淆矩阵说明了什么?

短答:
- 类别 3 极少,经常被预测为 class 2;v1/v2 的混淆结构没有本质改变。

意义:
- 这解释了为什么加入 actigraphy 后主表 Macro-F1 没有稳定提升。

边界:
- 当前混淆矩阵是代表性 `sklearn LR` 的 out-of-fold 预测,不是 12 个配置的完整混淆矩阵全集。

---

## 11. 这个项目和 P2 怎么衔接?

短答:
- P1 负责确定公平协议、baseline、特征版本和系统成本结论。P2 会把其中一个可部署模型推进到 MLOps pipeline。

P2 可做:
- MLflow Model Registry
- FastAPI 推理服务
- Docker/环境封装
- 数据/模型版本管理
- 监控与发布

推荐模型:
- 可以优先选择 sklearn LR 或 PyTorch MLP,因为推理延迟低、服务化简单、质量稳定。

---

## 12. 如果老师问"那 Spark 是不是没必要?"

推荐回答:

> 不是。我们的结论更细:Spark 不适合这个任务的小表格训练和单样本推理,但它仍然是大规模特征/ETL 阶段的合理候选。只是本机 local mode 和 exact per-participant 聚合这个实现下,Spark 没有赢过 streaming pandas。这反而说明系统设计不能只贴框架标签,必须根据数据形态和算法实测。

---

## 13. 如果老师问"明天之后还要补什么?"

推荐回答:

> P1 主线已经完成。后续如果继续补 P1,优先补 A1-A4 轻量消融作为附录;但课程项目主线更应该进入 P2 MLOps,把 P1 选出的稳定模型做成可注册、可服务、可监控的 pipeline。

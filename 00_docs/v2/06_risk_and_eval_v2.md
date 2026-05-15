# 风险登记册 + 统一评价协议 v2

- 文档编号: `MLSYS-2026S-CC-RISK-EVAL-v2`
- 日期: `2026-04-18`
- 作用: (1) 汇总 v1 各方案散落的风险条目,给每条分配 owner/等级/应对 SOP;(2) 锁定项目 1/2 的统一评价协议,让所有对比表、报告图表有公共尺子
- 对应 v1: 合并并扩展 `mlsys_project_charter_v1.md §8` 与 6 份 plan_v1 的 "风险" + "评价指标" 章节

## 0. 相对 v1 的改动点

| # | v1 | v2 | 原因 |
|---|---|---|---|
| 1 | 风险散落在 7 份文件里,无 owner/无级别 | 统一到本登记册,每条标 owner/等级/触发信号/SOP | 可跟踪,答辩可讲 |
| 2 | 评价指标在 4 份方案里不一致 | P1 锁 Macro-F1,P2 锁 QWK,各配 2 辅指标;系统指标 7 项统一 | 公共尺子 |
| 3 | 没有 WISDM 降级的 SOP | §6 给出具体切换步骤和时间估算 | 真能落地 |
| 4 | 远程 4090 的"窗口未知"无兜底 | §7 三级 GPU fallback,每级给出切换命令 | 最坏情况可控 |
| 5 | 无项目 done 定义 | §8 给出 P1/P2 各自"及格/良好/优秀"三档 DoD | 可自评 |

## 1. 风险登记册(总)

### 1.1 风险等级

- **L1** 低: 影响有限,可就地解决,不需通知导师
- **L2** 中: 影响一周以内的进度,需记便函并调整计划
- **L3** 高: 影响项目能否按期交付,需及时通知导师并启动预案

### 1.2 汇总表

| 编号 | 分类 | 风险描述 | 触发信号 | 级别 | Owner | 预案 §| 
|---|---|---|---|---|---|---|
| R-HW-1 | 硬件 | 远程 4090 使用窗口未确认 | W0 末仍无明确时段 | L3 | 成员 B | §7 三级 fallback |
| R-HW-2 | 硬件 | 5060 Ti sm_120 在 PyTorch stable 未 land | stable 通道跑 cuda kernel 报 `no kernel image` | L2 | 成员 B | §2 nightly 通道 |
| R-HW-3 | 硬件 | 本地磁盘 66 GiB 不够 | 脚本 `check_disk.sh` 返回 avail <10 GiB | L3 | 成员 A | §6 切 WISDM |
| R-HW-4 | 硬件 | 本地 RAM 31 GiB 不足加载 actigraphy | Pandas `MemoryError` | L2 | 成员 A | 强制走 Spark 流式;或换 polars 分块 |
| R-DATA-1 | 数据 | Kaggle API 国内连不上 | 3 次重试失败 | L2 | 成员 A | §3 镜像 fallback + 手动下载 |
| R-DATA-2 | 数据 | actigraphy 覆盖率低(可能仅 30-50%) | EDA 发现大量参与者无 actigraphy | L2 | 成员 A | 设计 `feat_v2` 为"可选加强",双分支模型支持单分支 |
| R-DATA-3 | 数据 | 缺失值处理策略对结果影响大 | 同模型不同 imputer 指标差异 >0.05 | L1 | 成员 A | 在 MLflow 记录 imputer 作为参数,消融实验 A1 专门做 |
| R-SYS-1 | 系统 | Spark 在模型训练阶段输给 sklearn(必然) | 训练耗时 Spark > sklearn,3K 样本 | L1 | 成员 A | 报告直接阐明,把 Spark 价值定位到特征阶段;这不是 bug 是洞见 |
| R-SYS-2 | 系统 | Spark 在特征阶段也输给 pandas(数据量不够) | W2 对比发现 pandas 快 | L2 | 成员 A | 加 actigraphy 合成放大实验(10x),找到 Spark 拐点 |
| R-SYS-3 | 系统 | sklearn / Spark / PyTorch 三方 MLP 默认 optimizer 不一致导致不公平 | 同 feat 下 Macro-F1 差异 >0.05 | L1 | 成员 A+B | 报告明说"默认超参下的差异不是算法差,是系统默认"|
| R-ML-1 | 建模 | champion QWK 提升 <0.03 | Optuna 跑完后仍不达标 | L2 | 成员 B | top-3 ensemble 作 champion;或放弃融合,用最佳单模型 |
| R-ML-2 | 建模 | Optuna 100 trials 超出远程 GPU 窗口 | 预估剩余时间 > 可用时间 | L2 | 成员 B | 降级至 50 trials + MedianPruner,或迁到 Kaggle Notebook |
| R-ML-3 | 建模 | 5-fold CV 各 fold 差异巨大 | std/mean > 0.15 | L1 | 成员 B | 检查数据切分是否有泄漏,换 StratifiedGroupKFold |
| R-MLOPS-1 | MLOps | ModelScope custom pipeline 对多输入支持不足 | W7 发布时报错 | L2 | 成员 C | 简化 `inference.py` 为纯 Python 函数,不走 Pipeline;先发 HF Hub |
| R-MLOPS-2 | MLOps | Docker 镜像 >2 GiB 超国内 registry 默认限额 | push 失败 | L1 | 成员 C | 改多阶段构建;CPU 镜像不装 torch GPU wheel |
| R-MLOPS-3 | MLOps | FastAPI `/predict` 在 Docker 内起不来 | `docker run` 后 curl 无响应 | L1 | 成员 C | 加 `/health`,先本地 python 跑通再 docker |
| R-PROC-1 | 流程 | 中期答辩日期学校通知与预设不一致 | 学校通知晚于 W4 | L1 | 全员 | 周历有缓冲,整体前移一周 |
| R-PROC-2 | 流程 | git 冲突频繁影响协作 | 每周 >3 次冲突 | L1 | 全员 | 按成员分 feature branch,主干只合并 PR,约定 CODEOWNERS |
| R-PROC-3 | 流程 | 组员时间不对齐 | 某周产出 <50% | L2 | 全员 | 每周 15-min standup(线上/线下均可),blocker 当场分派 |
| R-DOC-1 | 文档 | model_card 不合规被 Hub 拒 | 发布失败 | L1 | 成员 C | 用 HF Hub 官方 `CC-BY-4.0` 模板,先跑示例仓验证 |
| R-DOC-2 | 文档 | 最终报告引用定位不准 | 导师审阅反馈 | L1 | 全员 | §11 参考用 cc/ 各文件里已核实的链接 |

### 1.3 等级分布小结

- L3: 2 条(R-HW-1、R-HW-3)— 必须有主动监控和兜底
- L2: 9 条 — 每周 review 一次
- L1: 9 条 — 发生时处理即可

## 2. 评价协议(统一,跨 P1/P2)

### 2.1 主/辅指标锁定

| 项目 | 主指标 | 辅指标 | 为什么选主 |
|---|---|---|---|
| **P1** 系统对比 | `Macro-F1` | `QWK`、`Balanced Accuracy` | Macro-F1 对类别不平衡稳健,且对"同算法跨系统"对比更敏感(不被 majority class 主导) |
| **P2** MLOps | `QWK` | `Macro-F1`、`Log Loss` | QWK 是 Kaggle 官方指标,对齐竞赛标准;Log Loss 捕捉概率校准 |

### 2.2 系统指标(两项目共用)

统一列 7 项,所有模型的所有 run 都记录:

| 指标 | 定义 | 测量方法 |
|---|---|---|
| `train_time_s` | 训练总时长(wall-clock,不含环境启动) | `time.perf_counter()` 包住 fit/train 循环 |
| `epoch_time_s` | 单 epoch 时长(仅 PyTorch) | `time.perf_counter()` 包住 epoch |
| `inference_latency_us` | 单样本推理延迟 | 1000 次均值,预热 100 次 |
| `inference_throughput_sps` | 推理吞吐(samples/s) | batch=1024 | batch/elapsed |
| `peak_rss_gb` | 峰值驻留内存 | `psutil.Process().memory_info().rss` / 1024³ |
| `peak_gpu_mem_gb` | 峰值 GPU 显存(仅 PyTorch) | `torch.cuda.max_memory_allocated()` / 1024³ |
| `model_size_mb` | 序列化后模型大小 | `os.path.getsize(model_path)` / 1024² |

### 2.3 数据切分协议(两项目共用)

- **切分器**: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`
- **group**: `participant_id`(来自 PIU)
- **stratify**: `sii` 标签
- **保存**: `data/splits/stratified_group_kfold_seed42.csv`,列 `participant_id, fold_idx`
- **规则**: 所有模型、所有系统使用同一切分文件

### 2.4 指标计算约定

- `Macro-F1`: `sklearn.metrics.f1_score(y_true, y_pred, average='macro')`
- `QWK`: `sklearn.metrics.cohen_kappa_score(y_true, y_pred, weights='quadratic')`
- `Balanced Accuracy`: `sklearn.metrics.balanced_accuracy_score(y_true, y_pred)`
- `Log Loss`: `sklearn.metrics.log_loss(y_true, y_proba, labels=[0,1,2,3])`

### 2.5 CV 报告格式

最终报告所有指标格式统一为 `均值 ± 标准差(n_folds=5)`,如 `QWK = 0.418 ± 0.023`。

### 2.6 class_weight 策略

三系统默认均使用 `balanced`(或等价)对齐,避免某一系统默认平等权重而失真。

### 2.7 随机种子

全局 `seed=42`,包括:
- `numpy.random.seed(42)`
- `torch.manual_seed(42)`
- `torch.cuda.manual_seed_all(42)`
- sklearn `random_state=42`
- Spark 随机操作的 `seed=42`
- Optuna `sampler = TPESampler(seed=42)`

## 3. MLflow 记录约定

### 3.1 必记 params

`model_name`、`feat_version`、`data_version`、`system`(sklearn|spark|pytorch)、`algorithm`(lr|mlp|cnn|fusion)、`seed`、`optimizer`、`lr`、`bs`、`epochs`、`class_weight_policy`、`imputer`、`scaler`、`device`(cpu|5060ti|4090)

### 3.2 必记 metrics

全部 2.1 指标 + 全部 2.2 系统指标,每个 fold 单独记一次,外加 `*_mean` / `*_std` 总结。

### 3.3 必记 tags

`owner`(A|B|C)、`phase`(baseline|enhanced|advanced)、`is_final_candidate`(bool)、`git_sha`、`env_pinned_hash`

### 3.4 Artifacts

- `confusion_matrix.png`
- `training_curve.png`(仅 PyTorch)
- `feature_importance.png`(若支持)
- `model/`(MLflow flavor)
- `inference.py`
- `input_example.json`
- `output_example.json`

## 4. 可复现性清单

每份最终 run 必须能通过以下步骤复现:

1. `git checkout <sha>`
2. `pip install -r envs/pinned_{env}.txt`
3. `dvc pull` 或 `make data`
4. `make features`
5. `python -m src.experiments.<script> --run-id <mlflow_run_id>`
6. 结果应在 `±1%` 之内

## 5. 项目 DoD(及格 / 良好 / 优秀)

### 5.1 项目 1

| 档位 | 完成项 |
|---|---|
| **及格** | feat_v1 构建完成;三系统 LR 跑完对比表的 3 行;书面报告 P1 有结果和分析 |
| **良好** | + feat_v2 pandas vs Spark 对比 + 三系统 MLP 对比;消融 A1-A4 任选 2 项;雷达图 + 混淆矩阵 |
| **优秀** | + feat_v3 融合特征展示;Spark 并行度扫描曲线;actigraphy 合成放大的"Spark 拐点"实验;中期答辩现场 demo |

### 5.2 项目 2

| 档位 | 完成项 |
|---|---|
| **及格** | MLflow 记录 Level 1 完整 + Registry `baseline` 别名;ModelScope 发布 baseline 模型(或 MLP 最佳);书面报告 P2 |
| **良好** | + Level 2 完成;Optuna 50 trials;champion 别名就位;Docker `infer` 镜像构建通过;FastAPI `/predict` 本地可跑 |
| **优秀** | + Level 3 融合模型;Optuna 100 trials;champion QWK 较 baseline +0.05;HF Hub 镜像发布;两家平台对比章节;现场 curl demo |

## 6. WISDM 硬兜底切换 SOP

### 6.1 触发条件(任一)

- 磁盘占用 >55 GiB(`check_disk.sh` 返回 avail <11 GiB)
- Kaggle API 连续 72 小时无法下载 PIU
- W1 末仍未在 PIU 上跑通任一 baseline
- actigraphy 解析本地 OOM 且 Spark 流式方案尝试后仍不可行

### 6.2 切换步骤(~3 天)

1. 便函记录: `memos/memo_YYYYMMDD_switch_to_wisdm_v1.md`,写明触发原因
2. 下载 WISDM: 见 `05_runbook_v2.md` §3.4
3. 数据适配: 新增 `src/data/preprocess_wisdm.py`,输出 `feat_v1_wisdm` / `feat_v2_wisdm`
4. 任务重定义:
   - P1 标签: 6 类 HAR(Walking / Jogging / Upstairs / Downstairs / Sitting / Standing)
   - P1 主指标: `Macro-F1`(不变),辅: `Accuracy`(替换 QWK,因 HAR 非有序分类)
   - P2 主指标: `Macro-F1`(QWK 不适用)
5. 切分: 按 `participant_id` subject-wise split(WISDM 常规做法)
6. 改模型输入/输出: 模型代码 99% 可复用,只改 `num_classes`、`in_features` 等
7. 更新 `02_charter_v2.md` / `03_plan_p1_v2.md` / `04_plan_p2_v2.md` 的 P*_PIU 字样为 P*_WISDM
8. 继续推进

### 6.3 切换后的预期影响

- P1 的 Spark 价值场景从"actigraphy 预处理"变成"WISDM 298 万原始样本的模型训练",对比仍成立(而且更传统/更直观)
- P2 的多模态融合模型失去依据(WISDM 单模态),降级为"1D CNN / LSTM / Transformer"三层
- ModelScope 发布换个仓库名即可,model_card 重写输入格式部分

## 7. 三级 GPU Fallback SOP

### Tier 1(默认): 远程 4090

- 触发: 默认路径
- 配置: SSH key 双向,代码 rsync,MLflow SSH tunnel
- 风险: 窗口不稳定,需 W0 确认时段

### Tier 2: Kaggle Notebook

- 触发: Tier 1 连续 24 小时不可用,或窗口剩余 <10 小时
- 切换:
  1. 将代码 push 到 GitHub(私有仓)或打包上传 Kaggle Dataset
  2. 新建 Kaggle Notebook,附加 PIU 竞赛 dataset
  3. 启用 GPU (T4 x2)
  4. 在 notebook 里跑训练脚本
  5. 结果保存到 Kaggle output,下载回本地,重录入 MLflow
- 限制: 单次 session 9 小时,免费 30 小时/周
- 适合: 单次长训练、Optuna trials 小批量

### Tier 3: AutoDL / Colab Pro

- 触发: Tier 1 + Tier 2 都不可用
- AutoDL: 注册后 SSH 到实例,按 Tier 1 流程 rsync,按需开机关机,预算 ¥3-6/h × 20h ≈ ¥100
- Colab Pro: $9.99/月,T4 稳定
- 预算: 若要走 Tier 3,先用 `memos/memo_YYYYMMDD_tier3_trigger_v1.md` 记录并与组员对齐

### Tier 0(最坏情况): CPU 训练

- 触发: 所有 GPU 方案都失败
- 切换:
  - 模型层次降到 Level 1(tabular MLP / LR / CatBoost)
  - PyTorch MLP 用 CPU 跑(sklearn / PyTorch-CPU 差异不大)
  - 项目 2 的深度模型降级为 CatBoost + MLP 融合
  - Optuna trials 减到 30 次
- DoD 降为 "及格"

## 8. 决策节点(每周 review)

每周日晚 30 min standup,检查以下信号,必要时触发切换:

| 信号 | 来源 | 动作 |
|---|---|---|
| 磁盘 avail <10 GiB | `check_disk.sh` | 评估切 WISDM |
| 远程 4090 连续 3 天不可用 | B 手记 | 启动 Tier 2 |
| W 末 DoD 未完成度 <50% | TaskList | 调降 DoD 档位 |
| MLflow run 数 < 预期 50% | MLflow UI | 调整实验矩阵,删减 Level 3 |
| 任何 L3 风险被触发 | 本登记册 | 24h 内导师通告 |

## 9. 便函与决策记录

每次风险触发 / SOP 切换 / DoD 调整,**强制**写入一份便函:

- 路径: `00_docs/v1/memos/memo_YYYYMMDD_<topic>_v1.md`
- 模板: `00_docs/templates/mlsys_memo_template.md`
- 发起人: 相应 Owner
- 必填: 触发信号、决策、影响范围、下一步动作

答辩时这些便函串起来就是项目"过程记录",比只看最终结果更有说服力。

## 10. 修订记录

- `v2 | 2026-04-18`: 首版风险登记册与评价协议。v1 系列散落内容的整合 + 扩展;锁 P1=Macro-F1、P2=QWK 主指标;新增 WISDM 切换 SOP 与 GPU 三级 fallback;给 P1/P2 三档 DoD;每周 standup 的决策信号表。

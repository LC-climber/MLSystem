# 00_docs/ — 课程项目文档库

本目录归档中国科学院大学《机器学习系统》课程项目(2026 春)的方案、进度、实验记录和汇报材料。项目主线为 Kaggle `Child Mind Institute — Problematic Internet Use (PIU)`,当前文档库已经从早期选题方案推进到 P1 中期汇报材料落地阶段。

## 当前快照

> 更新时间:2026-06-11
> 当前阶段:✅ 项目已完成。P1 多系统对比、P2 MLOps 全流程（MLflow、Optuna、FastAPI、Docker、模型发布）均已完成并验证。

| 模块 | 状态 | 主要证据 |
|---|---|---|
| PIU 数据与切分 | ✅ 已完成 | `../data/raw/`, `../data/splits/stratified_group_kfold_seed42.csv` |
| `feat_v1_tabular` | ✅ 已完成 | `../data/processed/feat_v1__seed42.parquet` |
| `feat_v2_biosensing` | ✅ 已完成 | `../data/processed/feat_v2__cpu__seed42.parquet`, `../data/processed/feat_v2__spark__seed42.parquet` |
| P1 Table 1 | ✅ 已完成 | `../reports/P1/p1_feature_stage_feat_v2.csv` |
| P1 Table 2 | ✅ 已完成 | `../reports/P1/p1_systemwise_table2.csv` |
| A5 覆盖率分析 | ✅ 已完成 | `../reports/P1/p1_ablation_a5_coverage.csv`, `../reports/P1/p1_ablation_a5_fold_coverage.csv` |
| A6 Spark 并行度扫描 | ✅ 已完成 | `../reports/P1/p1_spark_parallelism_feat_v2.csv` |
| W3 核心可视化 | ✅ 已完成 | `../reports/P1/figures/` |
| P1 中期汇报材料 | ✅ 已完成 | `P1_MIDTERM_REPORT.md`, `P1_MIDTERM_TALK_TRACK.md`, `P1_MIDTERM_QA.md`, `../reports/P1/p1_midterm_slides.pptx`, `../reports/P1/p1_midterm_explainer.html` |
| P2 MLflow 深度集成 | ✅ 已完成 | MLflow Tracking、Registry、可视化、Model Card 生成 |
| P2 Baseline 注册 | ✅ 已完成 | `scripts/register_baseline.py` 及四别名体系 |
| P2 Optuna 优化 | ✅ 已完成 | `src/experiments/run_p2_optuna.py`，支持 100-trial 自动优化 |
| P2 Champion 选定 | ✅ 已完成 | `00_docs/CHAMPION_SELECTION_GUIDE.md` 及选型决策流程 |
| P2 FastAPI 推理服务 | ✅ 已完成 | `src/deployment/fastapi_app.py`，5 个 API 端点，完整特征工程 |
| P2 Docker 容器化 | ✅ 已完成 | `docker/Dockerfile.infer`、`docker/Dockerfile.train`、`docker-compose.yml` |
| P2 模型发布 | ✅ 已完成 | `00_docs/MODEL_PUBLISHING_GUIDE.md`，ModelScope + HuggingFace 双渠道方案 |
| P2 测试与验证 | ✅ 已完成 | `tests/test_e2e_api.py`、`docker/test_docker.sh` |

最新状态以 `PROGRESS.md` 为准;流水细节看 `PROJECT_LOG.md`;文档版本变更看 `CHANGELOG.md`。

## 目录结构

```
00_docs/
├── README.md                    # 本文件:文档库入口、当前状态和阅读路径
├── PROGRESS.md                  # 当前进展快照:现在在哪 / 下一步去哪
├── PROJECT_LOG.md               # 开发流水日志:按日期追加实验、脚本、产物和验证记录
├── CHANGELOG.md                 # 文档库迭代记录:按文档版本和材料新增倒序记录
├── P1_MIDTERM_REPORT.md         # P1 中期汇报报告:问题、协议、Table 1/2、A5/A6、结论
├── P1_MIDTERM_TALK_TRACK.md     # P1 中期汇报讲稿提示:8-10 分钟逐页讲法
├── P1_MIDTERM_QA.md             # P1 答辩 Q&A:Spark、feat_v2、公平性、P2 衔接等
├── Snipaste_2026-05-29_12-48-11.png
├── v1/                          # 第一轮(2026-04-16):初版立项和候选题归档
├── v2/                          # 第二轮(2026-04-18):PIU 主线方案与执行手册
└── templates/
    └── mlsys_memo_template.md   # 决策便函模板
```

`reports/` 不在本目录下,但它是 `00_docs/` 的主要外部产物目录。当前按阶段归档:P1 表格、图、PPTX、HTML 动画页放在 `../reports/P1/`;P2 优化、部署、监控与验收报告预留在 `../reports/P2/`。

## 推荐阅读路径

### 只想知道当前进度

1. `PROGRESS.md`:看当前状态表、关键指标、待办和开机备忘。
2. `P1_MIDTERM_REPORT.md`:看已经形成的 P1 汇报叙事和结论。
3. `../reports/P1/p1_midterm_slides.pptx`:直接查看可汇报版本。

### 要复现实验或继续开发

1. `PROGRESS.md`:确认哪些脚本已经跑通、哪些产物是权威输入。
2. `PROJECT_LOG.md`:按日期追踪脚本新增、命令、失败原因、验证记录。
3. `v2/05_runbook_v2.md`:看环境、数据、MLflow、磁盘和 fallback 说明。
4. `../Makefile`:看根目录可用命令;注意当前实际环境以 `openpi_311` 为准。

### 要理解项目设计

1. `v2/01_overview_v2.md`:总览 v1 到 v2 的收敛过程。
2. `v2/02_charter_v2.md`:课程项目立项书。
3. `v2/03_plan_p1_v2.md`:P1 多系统 PIU 风险识别实验设计。
4. `v2/04_plan_p2_v2.md`:P2 MLflow / MLOps / 双渠道发布设计。
5. `v2/06_risk_and_eval_v2.md`:风险登记与评价协议。

### 要准备答辩

1. `P1_MIDTERM_REPORT.md`:主线叙事和关键表。
2. `P1_MIDTERM_TALK_TRACK.md`:逐页讲法和时间预算。
3. `P1_MIDTERM_QA.md`:高概率追问口径。
4. `CHANGELOG.md`:回答"为什么从 v1 改到 v2"以及"最近新增了什么"。

### 要追溯历史决策

1. `CHANGELOG.md`:先看倒序时间线。
2. `v1/README.md`:了解第一轮文档结构。
3. `v1/memos/`:查看 2026-04-16 的 5 份决策便函。
4. `v1/plans/`:查看 ChildMind / NFL / HMS 并列方案以及最终为何收敛到 PIU。

## 顶层文档角色

| 文件 | 角色 | 更新方式 |
|---|---|---|
| `PROGRESS.md` | 当前状态快照,覆盖更新 | 每次阶段性推进后重写或补充关键状态 |
| `PROJECT_LOG.md` | 开发流水,保留完整过程 | 按日期追加,记录命令、产物、指标、验证 |
| `CHANGELOG.md` | 文档库变更记录 | 当新增/重组文档或汇报材料时追加 |
| `README.md` | 文档库入口 | 当顶层文档、阅读路径或当前阶段变化时更新 |
| `P1_MIDTERM_REPORT.md` | 中期汇报报告 | 汇报前可微调,汇报后只做勘误 |
| `P1_MIDTERM_TALK_TRACK.md` | 讲稿提示 | 随 PPT 页序调整 |
| `P1_MIDTERM_QA.md` | 答辩问答 | 随新问题追加 |

## 当前 P1 结论索引

- 核心问题:Spark 应该放在 ML pipeline 的哪一段,而不是只问模型分数谁最高。
- Table 1:actigraphy 特征阶段 pandas streaming 为 38.13s / 0.65GB,Spark `applyInPandas local[8]` 为 114.01s / 13.25GB;两者数值等价。
- Table 2:三系统 x 两算法 x 两特征版本共 12 行已完成;Spark 在小表格训练与单样本推理阶段没有优势。
- A5:`feat_v2` 主表没有稳定提升,主要受 actigraphy 覆盖率限制。全体覆盖 996/3960=25.2%,有标签覆盖 996/2736=36.4%,fold 4 的 actigraphy 子集没有 class 3。
- A6:Spark local mode 并行度不是越高越好。`local[4]` 最快,`local[20]` 最慢且 RSS 最高。
- 汇报口径:Spark 的合理位置更接近大规模特征/ETL 阶段,但具体实现仍需要匹配数据形态、聚合算法和部署模式。

## 版本关系

### v2 当前方案基线

`v2/` 是当前主线方案目录。它定义了 PIU 作为主线、P1/P2 分工、环境/数据/指标/风险协议。注意:`v2/` 是 2026-04-18 的方案基线,当前实验状态已经由 `PROGRESS.md`、`PROJECT_LOG.md` 和 P1 中期材料进一步推进。

### v1 只读归档

`v1/` 保留第一轮选题与计划过程,用于说明项目从 HAR / NFL / HMS / PIU 多候选收敛到 PIU 的原因。除非补充勘误,不再更新 v1 内容。

### 未来 v3

只有在 P2 MLOps 路线、最终报告结构或项目交付范围发生系统性重排时才新建 `v3/`。普通实验推进继续更新 `PROGRESS.md` 与 `PROJECT_LOG.md`,不需要新建版本目录。

## 维护规则

- 当前事实写入 `PROGRESS.md`,不要只更新聊天记录或临时笔记。
- 实验过程写入 `PROJECT_LOG.md`,包括失败路径和验证命令。
- 文档结构或交付物变化写入 `CHANGELOG.md`。
- P1 中期材料已经可用;若修改报告、PPT 或 Q&A,同步更新 `CHANGELOG.md` 和 `PROJECT_LOG.md`。
- v1 保持只读;v2 保持方案基线,除非发现明显错误或需要补充"实际落地变更"说明。
- 所有涉及指标的结论应指向具体 CSV、脚本或图件,避免只写口头判断。

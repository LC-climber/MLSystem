# 文档库迭代记录

按时间倒序记录 `00_docs/` 下所有文档的版本变迁、关键决策与迁移说明。每次产生新一轮 vN 文档时,在表头追加一段。

---

## 2026-05-31 — 环境方案落地校正(README / runbook / charter 对齐实现)

修正实现与文档的矛盾:`README.md`、`v2/05_runbook_v2.md`、`v2/02_charter_v2.md` 仍写"三套 conda 环境(`mlsys_cpu/gpu_local/gpu_remote`)+ `setup_envs.sh`",而 2026-05-29 实际落地已改为**复用单一 `openpi_311` 环境**(PyTorch 2.9.0+cu128,原生支持 sm_120)。矛盾根因:`README.md`(05-29 12:24)写于环境决策(~12:30)之前,此后未回改。

- `../README.md`:环境搭建 / 开发流程 / 环境说明 / 当前状态四处改为 openpi_311;当前状态更新到 W2(三系统对比表 1 已完成)。
- `v2/05_runbook_v2.md`:顶部与 §2 加"实际落地变更"提示,TL;DR step 1 改为激活 openpi_311;§3 数据 / §4 MLflow / §5 磁盘 / §6 VRAM / §7 GPU fallback 仍有效。
- `v2/02_charter_v2.md`:§2.2 环境矩阵下补落地变更注记。
- 三套环境矩阵内容**保留**作设计依据与异机 / 多环境重建参考,不删除。
- 环境真相单一来源:[`../envs/README.md`](../envs/README.md) + `PROJECT_LOG.md`。

---

## 2026-05-15 — 文档库重组

非内容性变更:目录结构调整,便于阅读与追溯。

- 新建 `v1/` 与 `v2/` 顶层目录,按迭代轮次物理隔离 14 份 v1 文档与 6 份 v2 文档。
- 原 `cc/` 目录(v2 的临时命名)更名为 `v2/`。
- 原根目录下的 `mlsys_project_charter_v1.md`、`kaggle_competition_candidates_v1.md` 移入 `v1/`。
- 原 `memos/`、`plans/` 子目录整体移入 `v1/`。
- 全量更新文档内 `00_docs/...` 路径引用,匹配新结构。
- 新增 `00_docs/README.md`、`00_docs/v1/README.md`、`00_docs/v2/README.md` 与本 CHANGELOG。
- `templates/` 不动,保留在顶层(跨版本通用)。

无文档内容(章节、结论、数据)被修改。

---

## v2 — 2026-04-18:收敛优化

**状态**: 当前活跃版本。`v2 draft`,待课程组 review 后转 `v2 decided`。

### 背景

v1 在两天的密集决策后留下两个问题:**主线未收敛**(charter 推 HAR、portfolio 推 Kaggle 三题)与**落地细节不足**(Spark 在小数据上的"伪分布式悖论"、PyTorch 版本过时、磁盘无预算、评价指标四份方案不一致)。v2 不重新选题,而是将 v1 已有共识收紧成一套可执行文件。

### 三项关键决策(D1-D3)

| 决策 | v1 现状 | v2 决策 |
|---|---|---|
| D1 主线选题 | HAR 与 Kaggle 三题并列 | **PIU 为主**(Kaggle Child Mind Institute),WISDM 为硬兜底 |
| D2 发布通道 | 只 ModelScope | **ModelScope 主 + HuggingFace Hub 镜像**,互为 fallback |
| D3 团队分工 | 3 人或 2 人两种写法 | **3 人**:A=数据+Spark / B=深度学习 / C=MLOps+发布 |

### 产出 6 份文件(`v2/`)

| 文件 | 角色 | 替代/合并的 v1 文件 |
|---|---|---|
| `01_overview_v2.md` | 总览 + 决策 + 新旧对照 | 替代 portfolio + 5 便函的"汇总"功能 |
| `02_charter_v2.md` | 修订版立项书 | 替代 `mlsys_project_charter_v1.md` |
| `03_plan_p1_v2.md` | 项目 1 主线执行版 | 替代 `plan_p1_childmind_piu_v1.md` |
| `04_plan_p2_v2.md` | 项目 2 主线执行版 | 替代 `plan_p2_childmind_piu_v1.md` |
| `05_runbook_v2.md` | 环境/数据/命令/预算 | 全新增,v1 系列无对应 |
| `06_risk_and_eval_v2.md` | 风险登记册 + 统一评价协议 | 合并 v1 各方案散落的"风险" / "指标"段 |

### v1→v2 主要技术变更

详见 `v2/01_overview_v2.md` §5 的 14 条对照表(O1-O14)。要点:

- Spark 阵地从"模型训练"挪到 actigraphy 时序预处理,真有数据量。
- 环境从 `torch 2.7.x + cu128` 升级到 `torch 2.11 stable`(远程 4090)+ `2.10 nightly`(本地 5060 Ti sm_120)。
- 评价指标:P1 锁 Macro-F1,P2 锁 QWK,各配 2 辅指标。
- MLOps 从 2 件套扩展为 6 件套(MLflow + DVC + Docker + FastAPI + Makefile + 双发布)。
- 磁盘 66 GiB 给出 7 项预算表,留 15 GiB 冗余,超预算自动切 WISDM。
- 项目时间从"大阶段"细化到 W0-W9 的 10 周周历,锁中期(W4)和最终(W9)两个硬锚点。

### 弃用与归档

- `v1/plans/plan_p1_nfl_bdb_v1.md` / `plan_p2_nfl_bdb_v1.md`:NFL Prediction 报名截止已过(2025-11-26)。
- `v1/plans/plan_p1_hms_hbac_v1.md` / `plan_p2_hms_hbac_v1.md`:不适合三系统公平对比。
- 上述 4 份保留只读,作为决策遗产归档,不再更新。

### 持续有效的 v1 文件

- `v1/memos/` 全部 5 份便函:决策时间线证据。
- `v1/kaggle_competition_candidates_v1.md`:候选题筛选过程记录。
- `templates/mlsys_memo_template.md`:后续新便函仍按此格式写。

---

## v1 — 2026-04-16:初版立项

**状态**: 已归档,只读。主线已被 v2 收敛到 PIU。

### 背景

课程项目立项第一日。`2026-04-17` 前要交一版可提交的项目计划,因此当天连续做了 5 次决策(对应 5 份便函),并产出 1 份立项书 + 1 份 Kaggle 候选题整理 + 6 份并列计划书(P1/P2 × Child Mind/NFL/HMS) + 1 份 portfolio 索引。

### 产出 14 份文件(`v1/`)

**立项主线**

- `mlsys_project_charter_v1.md`:课程项目立项与计划。主线 HAR(WISDM/PAMAP2),备选 UrbanSound8K。
- `kaggle_competition_candidates_v1.md`:Kaggle 竞赛题目筛选,7 题分级排序。

**5 份决策便函**(`v1/memos/`,均 2026-04-16)

| 编号 | 主题 | 关键结论 |
|---|---|---|
| MEMO-01 | 项目初始化 | 主线 HAR、备选 UrbanSound8K |
| MEMO-02 | 硬件条件确认 | 本地 i5-14600K + 31 GiB + 66 GiB 盘,远程单卡 4090 |
| MEMO-03 | GPU 环境约束 | 本地 5060 Ti 需 PyTorch ≥ 2.7.0 + cu128(注:已被 v2 升级) |
| MEMO-04 | Kaggle 候选题初筛 | 第一梯队 PIU / NFL / HMS |
| MEMO-05 | 项目计划书包成稿 | 6 份并列计划完成,待收敛 |

**6 份并列计划 + 1 portfolio**(`v1/plans/`)

| 文件 | 题目 | v2 状态 |
|---|---|---|
| `plan_p1_childmind_piu_v1.md` | PIU 多系统对比 | **被 v2 选为主线**,已替代 |
| `plan_p2_childmind_piu_v1.md` | PIU MLOps | **被 v2 选为主线**,已替代 |
| `plan_p1_nfl_bdb_v1.md` | NFL 多系统对比 | 弃用(报名截止) |
| `plan_p2_nfl_bdb_v1.md` | NFL MLOps | 弃用 |
| `plan_p1_hms_hbac_v1.md` | HMS EEG 多系统对比 | 弃用(不适合公平对比) |
| `plan_p2_hms_hbac_v1.md` | HMS MLOps | 弃用 |
| `project_plan_portfolio_v1.md` | 6 份计划的总览索引 | 被 v2/01_overview_v2.md 替代 |

### v1 内部信息一览

- 全部文档统一用 `MLSYS-2026S-*` 命名前缀。
- 便函使用 `templates/mlsys_memo_template.md` 模板。
- 立项主线与 portfolio 候选题的不一致是 v2 收敛的主要驱动力。

---

## 模板与跨版本资源

- `templates/mlsys_memo_template.md`:便函通用模板,跨 v 版本复用。
- 命名规则:`memo_YYYYMMDD_<topic>_v{N}.md`,放在所属轮次的 `vN/memos/` 下。

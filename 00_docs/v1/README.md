# v1 — 初版立项(2026-04-16)

> **状态**: 已归档,只读。主线已被 v2 收敛到 PIU,新决策请到 [`../v2/`](../v2/)。

## 这一轮做了什么

课程项目立项第一日,2026-04-17 前需提交一版项目计划,因此当天连续完成 5 次决策(对应 5 份便函),并产出 1 立项书 + 1 候选题 + 6 并列计划 + 1 portfolio 索引,共 14 份文件。

主线在本轮锁定为 **HAR**(WISDM / PAMAP2),备选 UrbanSound8K;同时整理了 7 题 Kaggle 候选,作为后续可能的题目池。两条线并行,**未在本轮收敛**,这是 v2 重做的主要驱动力。

## 文件清单

### 立项与候选

| 文件 | 内容 |
|---|---|
| [`mlsys_project_charter_v1.md`](./mlsys_project_charter_v1.md) | 立项与计划。主线 HAR,备选 UrbanSound8K |
| [`kaggle_competition_candidates_v1.md`](./kaggle_competition_candidates_v1.md) | Kaggle 竞赛题筛选,7 题分级排序 |

### 决策便函(`memos/`,5 份,均 2026-04-16)

| 编号 | 文件 | 主题 |
|---|---|---|
| 01 | [memo_20260416_project_init_v1.md](./memos/memo_20260416_project_init_v1.md) | 项目第一版立项 |
| 02 | [memo_20260416_hardware_constraints_v1.md](./memos/memo_20260416_hardware_constraints_v1.md) | 硬件资源确认与方案收敛 |
| 03 | [memo_20260416_gpu_env_constraints_v1.md](./memos/memo_20260416_gpu_env_constraints_v1.md) | 本地 5060 Ti 与远程 4090 的环境约束 |
| 04 | [memo_20260416_kaggle_candidates_v1.md](./memos/memo_20260416_kaggle_candidates_v1.md) | Kaggle 竞赛候选题初筛 |
| 05 | [memo_20260416_plan_package_v1.md](./memos/memo_20260416_plan_package_v1.md) | 三组候选题六份计划书成稿 |

### 并列计划书(`plans/`)

| 文件 | 题目 | v2 状态 |
|---|---|---|
| [project_plan_portfolio_v1.md](./plans/project_plan_portfolio_v1.md) | 6 份计划的总览索引 | 被 `v2/01_overview_v2.md` 替代 |
| [plan_p1_childmind_piu_v1.md](./plans/plan_p1_childmind_piu_v1.md) | PIU 多系统对比 | **v2 主线**,被 `v2/03_plan_p1_v2.md` 替代 |
| [plan_p2_childmind_piu_v1.md](./plans/plan_p2_childmind_piu_v1.md) | PIU MLOps | **v2 主线**,被 `v2/04_plan_p2_v2.md` 替代 |
| [plan_p1_nfl_bdb_v1.md](./plans/plan_p1_nfl_bdb_v1.md) | NFL 多系统对比 | 弃用(报名截止 2025-11-26) |
| [plan_p2_nfl_bdb_v1.md](./plans/plan_p2_nfl_bdb_v1.md) | NFL MLOps | 弃用 |
| [plan_p1_hms_hbac_v1.md](./plans/plan_p1_hms_hbac_v1.md) | HMS EEG 多系统对比 | 弃用(不适合三系统公平对比) |
| [plan_p2_hms_hbac_v1.md](./plans/plan_p2_hms_hbac_v1.md) | HMS MLOps | 弃用 |

## 为什么保留这些已弃用文件

- 答辩时需要回答"你们是怎么选题的",这 14 份文件就是证据链。
- 5 份便函按时间顺序展示了一天内 5 次决策的演化。
- 4 份被弃用的 NFL/HMS 计划展示了"考虑过但理性放弃"的过程。

## 与 v2 的对应关系

详见 [`../CHANGELOG.md`](../CHANGELOG.md) 与 [`../v2/01_overview_v2.md`](../v2/01_overview_v2.md) §5 的 14 条对照表。

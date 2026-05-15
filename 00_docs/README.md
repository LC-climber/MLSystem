# 00_docs/ — 课程项目文档库

中国科学院大学《机器学习系统》课程项目(2026 春)的全部文档归档。本目录按**迭代轮次**组织,每一轮的产出物物理隔离,迭代关系与决策线索集中在 [CHANGELOG.md](./CHANGELOG.md)。

## 目录结构

```
00_docs/
├── README.md           # 本文件:目录导览
├── CHANGELOG.md        # 迭代时间线与决策记录
├── v1/                 # 第一轮(2026-04-16):初版立项,主线 HAR
│   ├── README.md
│   ├── mlsys_project_charter_v1.md
│   ├── kaggle_competition_candidates_v1.md
│   ├── memos/          # 5 份决策便函
│   └── plans/          # 6 份并列子方案 + 1 份 portfolio 索引
├── v2/                 # 第二轮(2026-04-18):收敛优化,主线 PIU(当前活跃)
│   ├── README.md
│   ├── 01_overview_v2.md
│   ├── 02_charter_v2.md
│   ├── 03_plan_p1_v2.md
│   ├── 04_plan_p2_v2.md
│   ├── 05_runbook_v2.md
│   └── 06_risk_and_eval_v2.md
└── templates/
    └── mlsys_memo_template.md
```

## 当前活跃版本

**v2**(2026-04-18 起)。新成员、新决策、新便函全部以 v2 为基准。

v1 文档保留为只读归档,用于答辩时展示选题和路线收敛过程,不再更新。

## 推荐阅读路径

- **新组员入门**:从 [v2/README.md](./v2/README.md) 开始,按其中给出的 6 份文件顺序读完即可开机。
- **了解决策过程**:先读 [CHANGELOG.md](./CHANGELOG.md),再按需查看 [v1/](./v1/) 中的便函。
- **答辩准备**:[v2/01_overview_v2.md](./v2/01_overview_v2.md) §5 的"v1→v2 优化对照表"可直接作为问答素材。
- **追踪历史决策**:[v1/memos/](./v1/memos/) 中 5 份便函按时间顺序记录了 2026-04-16 当天 5 次关键决策。

## 文档命名约定

- v 系列产出物均带 `_v{N}` 后缀,N 单调递增。
- 便函命名:`memo_YYYYMMDD_<topic>_v{N}.md`,模板见 [templates/mlsys_memo_template.md](./templates/mlsys_memo_template.md)。
- 跨版本文件保持文件名稳定,只在不同版本目录下并存,便于 diff。

## 后续迭代

- 中期答辩前(预计 2026-05 下旬)可能产生 v3,届时新建 `v3/` 目录,旧版自动归档。
- 课程作业最终交付物(报告 / PPT / 视频脚本)按 `reports/` `slides/` 等子目录组织,届时在本 README 与 CHANGELOG 中追加。

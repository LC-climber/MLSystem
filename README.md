# MLSystem — 机器学习系统课程项目(2026 春)

中国科学院大学《机器学习系统》课程的两项作业实现:

- **项目 1**: 多系统问题性互联网使用风险识别算法对比(单机 / 分布式 / 深度学习)
- **项目 2**: 基于 MLflow 的 PIU 风险识别 MLOps 实践与双渠道发布

主线数据为 Kaggle [Child Mind Institute — Problematic Internet Use](https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use),WISDM HAR 作为硬兜底。

## 仓库结构

```
.
├── 00_docs/            # 课程项目全部文档(立项书、计划、便函、风险评估)
│   ├── README.md       # 文档库导览
│   ├── CHANGELOG.md    # v1 → v2 迭代记录
│   ├── v1/             # 2026-04-16 初版立项(已归档,只读)
│   ├── v2/             # 2026-04-18 收敛优化(当前活跃版本)
│   └── templates/      # 跨版本通用模板
└── README.md           # 本文件
```

代码、数据、实验目录在后续 W0 启动后按 `v2/05_runbook_v2.md` 的规划逐步建立。

## 当前阶段

`v2 draft` — 文档已收敛,等待课程组 review 后转 `v2 decided`,然后进入 W0 环境与数据搭建。

## 快速入门

1. 想了解项目是什么:读 [`00_docs/v2/01_overview_v2.md`](./00_docs/v2/01_overview_v2.md)(5 分钟)。
2. 想开机干活:读 [`00_docs/v2/05_runbook_v2.md`](./00_docs/v2/05_runbook_v2.md)(20 分钟)。
3. 想了解决策过程:读 [`00_docs/CHANGELOG.md`](./00_docs/CHANGELOG.md)。

## 团队

3 人小组(姓名待填):

| 角色 | 职责 |
|---|---|
| A | 数据获取与单机 / Spark 实验 |
| B | 深度学习与远程 GPU 训练 |
| C | MLOps、推理服务与双渠道发布 |

详细周历分工见 [`00_docs/v2/02_charter_v2.md`](./00_docs/v2/02_charter_v2.md)。

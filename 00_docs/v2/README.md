# v2 — 收敛优化版(2026-04-18)

> **状态**: 当前活跃版本(`v2 draft`)。新成员入门、新决策、新便函都以本目录为基准。

## 这一轮做了什么

v1 在两天密集决策后留下两个问题:**主线未收敛**(charter 推 HAR、portfolio 推 Kaggle 三题)和**落地细节不足**(Spark 伪分布式悖论、PyTorch 版本过时、磁盘无预算、评价指标四份方案不一致)。

v2 不重新选题,而是把 v1 已有的共识收紧成一套可执行文件。三项关键决策:

| 决策 | v1 现状 | v2 决策 |
|---|---|---|
| D1 主线选题 | HAR 与 Kaggle 三题并列 | **PIU 为主**(Kaggle Child Mind Institute),WISDM 为硬兜底 |
| D2 发布通道 | 只 ModelScope | **ModelScope 主 + HuggingFace Hub 镜像**,互为 fallback |
| D3 团队分工 | 3 人或 2 人两种写法 | **3 人**:A=数据+Spark / B=深度学习 / C=MLOps+发布 |

## 文件清单(6 份)

| 序号 | 文件 | 角色 | 阅读时间 |
|---|---|---|---|
| 01 | [01_overview_v2.md](./01_overview_v2.md) | 总览 + 三项决策 + v1→v2 14 条对照 | 5 min |
| 02 | [02_charter_v2.md](./02_charter_v2.md) | 修订版立项书:选题、命名、环境、里程碑 | 20 min |
| 03 | [03_plan_p1_v2.md](./03_plan_p1_v2.md) | 项目 1 主线执行版:多系统 PIU 对比 | 40 min |
| 04 | [04_plan_p2_v2.md](./04_plan_p2_v2.md) | 项目 2 主线执行版:PIU MLOps 与双发布 | 40 min |
| 05 | [05_runbook_v2.md](./05_runbook_v2.md) | 落地手册:环境/数据/命令/磁盘预算 | 20 min |
| 06 | [06_risk_and_eval_v2.md](./06_risk_and_eval_v2.md) | 风险登记册 + 统一评价协议 | 15 min |

## 推荐阅读顺序

1. `01_overview_v2.md` — 把握全局
2. `02_charter_v2.md` — 选题与里程碑
3. `05_runbook_v2.md` — 知道怎么开机
4. `03_plan_p1_v2.md` — P1 实验设计
5. `04_plan_p2_v2.md` — P2 MLOps 全流程
6. `06_risk_and_eval_v2.md` — 出事了怎么办

## 与 v1 的关系

- v2 是 v1 的"收敛 + 加深",不是平地起高楼。每一份 v2 文件顶部都有"相对 v1 的改动点"小段。
- 历史文档全部保留在 [`../v1/`](../v1/),不删除、不再更新。
- 详细对照见 [`./01_overview_v2.md`](./01_overview_v2.md) §5 与 [`../CHANGELOG.md`](../CHANGELOG.md)。

## 本 v2 没有解决的事

(节选自 `01_overview_v2.md` §7,这里提示读者必看)

- 远程 4090 使用窗口未确认,只给了 fallback,没给保证。
- actigraphy 全量加载在本地 31 GiB RAM 是否 OOM 未实测。
- Kaggle API 国内偶发连接失败,镜像 fallback 已列但非全保。
- ModelScope "时序+tabular 双输入"模板缺失,需 custom pipeline。
- 中期答辩日期未确认,默认排在 5 月下旬。

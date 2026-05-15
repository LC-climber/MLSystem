# 《机器学习系统》课程项目优化方案总览 v2

- 文档编号: `MLSYS-2026S-CC-OVERVIEW-v2`
- 课程名称: `机器学习系统`
- 优化日期: `2026-04-18`
- 作者角色: `Claude Code 对 00_docs/v1/ 系列文档的评审与优化`
- 优化基准: `/home/er/桌面/MLsystem/00_docs/v1/**/*.md`(共 14 份)
- 产出目录: `/home/er/桌面/MLsystem/00_docs/v2/`
- 状态: `v2 draft`,待课程组 review 后转 `v2 decided`

## 0. 速读版: 如果只读一页

- 课程两项作业的主线**统一到 Kaggle `Child Mind Institute — Problematic Internet Use (PIU)`**,`WISDM HAR` 作硬兜底。
- Spark 在小数据上的"伪分布式悖论"用 **actigraphy 原始加速度时序预处理阶段** 解决,不再在 3000 行样本训练中强行比 Spark 与 sklearn。
- PyTorch 版本从 `2.7.x` 升到 `2.11 stable + cu128`,本地 5060 Ti(sm_120)明确 **nightly 通道**。
- 磁盘预算落地到每类产物的 GB 数,66 GiB 硬上限下留 15 GiB 冗余;超预算自动降级 WISDM。
- 评价指标全局统一: **P1 主 Macro-F1,P2 主 QWK**,各配 2 辅指标。
- MLOps 从"MLflow+ModelScope"扩展为 "MLflow + DVC/git-lfs + Docker + FastAPI + ModelScope 主 + HF Hub 镜像"。
- 6 份并列子方案收敛为"1 份主线执行版 + 1 份备选摘要"。
- 周历化时间计划锁定中期(5 月下旬)和最终(6 月底)两个硬锚点。

## 1. 为什么重做一版(Context)

当前 `00_docs/v1/` 已存在一套完整文档集(1 份立项书 + 1 份候选题整理 + 5 份便函 + 1 份 portfolio + 6 份并列子方案)。这些文档在决策初期有价值,但存在以下影响落地的问题:

- **选题决策未收敛**: `charter_v1` 以 HAR(WISDM/PAMAP2)为主线,`portfolio_v1` 又推 3 个 Kaggle 题并生成 6 份并列计划书,两套主线互不相容。
- **分布式系统的科学性存疑**: PIU/NFL 都是小数据,Spark 在模型训练阶段必输给 sklearn,报告结论易流于"做了白做"。
- **技术栈事实已变**: PyTorch stable 已到 `2.11`,`5060 Ti (sm_120)` 到 2025-10 仍需 nightly,原写法 `2.7.x + cu128` 过时。
- **硬件约束未量化**: 66 GiB 磁盘、无 VRAM 分级、远程 4090 无 fallback。
- **评价协议四份方案不一致**: 各用 Acc / Macro-F1 / Weighted-F1 / QWK / LogLoss 等不同主指标,报告横向对比无公共尺子。
- **落地细节不足**: 数据获取、环境锁定、MLOps 深度、团队分工都停留在口号层面。

因此,本 v2 版方案的目标不是"重新选题",而是**把 v1 已有的共识收紧到一套可执行文件**,让任何一名新组员拿到 `00_docs/v2/` 目录后,一天内能开机工作。

## 2. 本次优化的最终决策

三项关键决策已经在与用户讨论后锁定:

| # | 决策项 | v1 现状 | v2 决策 |
|---|---|---|---|
| D1 | 主线选题 | HAR 与 Kaggle 三题并列,无收敛 | **PIU 为主,WISDM 为硬兜底**(磁盘/数据受阻时无缝切) |
| D2 | 发布通道 | 只 ModelScope | **ModelScope 主 + HuggingFace Hub 镜像**(互为 fallback) |
| D3 | 团队分工 | 3 人或 2 人两种写法并列 | **3 人**: A=数据与单机+Spark / B=深度学习 / C=MLOps+发布 |

## 3. 硬件条件(重新量化)

### 3.1 本地

| 项 | 规格 |
|---|---|
| CPU | Intel Core i5-14600K,20 逻辑核 |
| RAM | 31 GiB |
| 磁盘(可用) | **66 GiB**(硬上限) |
| GPU | RTX 5060 Ti,假设 **16 GB VRAM**(若为 8 GB 版需调整 batch 映射) |
| GPU 架构 | Blackwell,**sm_120** |
| 最低驱动 | `R570+` |
| OS | Linux(项目强烈推荐 Linux/WSL2,Windows 原生 sm_120 兼容更差) |
| Conda | `25.7.0` 已验证 |

### 3.2 远程

| 项 | 规格 |
|---|---|
| GPU | 单卡 RTX 4090(24 GB VRAM,sm_89) |
| 使用窗口 | **未知**(需走三级 fallback,见 `06_risk_and_eval_v2.md`) |

### 3.3 关键事实更新(来自 2026-04-18 web 搜索)

- PyTorch **stable 已到 2.11.0**(PyPI 默认 cu130)。
- `cu130` 只覆盖 Turing (sm_75)+,**不支持 sm_120**,5060 Ti 必须走 cu128/cu129 轮子。
- **截至 2025-10 stable PyTorch (2.9/2.10) 尚未完整支持 sm_120**,5060 Ti 需 `nightly 2.10.0.dev+cu128`。
- 已验证工作组合: `Linux/WSL2 + Python 3.11 + CUDA 12.8.1 + cuDNN 9.x + PyTorch 2.10+ nightly + R570+ 驱动`。
- 远程 4090 (sm_89) 完全兼容 stable 2.11,无需 nightly。
- PIU 数据规模: **~3000 参与者 + actigraphy 原始加速度时序**,目标 `SII` 有序分类,官方指标 `Quadratic Weighted Kappa`。
- NFL BDB 2026: `Prediction` 报名截止日已过(2025-11-26),`Analytics` 无统一标签,不适合"同算法三系统对比",已从主线候选中剔除。

## 4. 优化方案文件结构(`00_docs/v2/`)

6 份文件,对原 14 份 v1 文档的内容做了压缩 + 重组:

| 文件 | 角色 | 对应 v1 的文件 |
|---|---|---|
| `01_overview_v2.md` | **本文档**。总览 + 决策 + 新旧对照 | 替代 `project_plan_portfolio_v1.md` + 5 份便函的"汇总"功能 |
| `02_charter_v2.md` | 修订版立项书 | 替代 `mlsys_project_charter_v1.md` |
| `03_plan_p1_v2.md` | 项目 1 主线执行版 | 替代 `plan_p1_childmind_piu_v1.md`,弃用 NFL/HMS 的 P1 |
| `04_plan_p2_v2.md` | 项目 2 主线执行版 | 替代 `plan_p2_childmind_piu_v1.md`,弃用 NFL/HMS 的 P2 |
| `05_runbook_v2.md` | 落地手册(环境/数据/命令/预算) | v1 系列没有对应文件,**新增** |
| `06_risk_and_eval_v2.md` | 风险登记册 + 评价协议 | 合并并强化 v1 各方案零散的 "风险" 与 "评价指标" 段 |

### 4.1 废弃的 v1 文件(保留只读,不再更新)

- `plan_p1_nfl_bdb_v1.md` / `plan_p2_nfl_bdb_v1.md`
- `plan_p1_hms_hbac_v1.md` / `plan_p2_hms_hbac_v1.md`

这些文件不删除,作为"决策阶段的遗产"归档,便于答辩时说明选题过程。

### 4.2 继续有效的 v1 文件

- `memos/*` 全部 5 份便函:记录决策时间线,答辩时可作证据
- `templates/mlsys_memo_template.md`:后续新便函仍按此写
- `kaggle_competition_candidates_v1.md`:候选题筛选过程记录

## 5. 相对 v1 的优化对照表

这是本次优化的核心产出。每一条写成 `[v1 问题] → [v2 改动] → [为什么更好]`,便于答辩时一问一答:

| # | v1 问题 | v2 改动 | 为什么更好 |
|---|---|---|---|
| **O1** | charter 选 HAR,portfolio 选 Kaggle,两条线并列,谁是主线不明确 | 单选 PIU 作主线,WISDM 作硬兜底;弃用 NFL/HMS 的 4 份子方案 | 消除决策悖论,节省并行维护成本;课程精力集中在一条叙事主线上 |
| **O2** | PIU 训练集仅 ~3000 行,Spark 在模型训练阶段必输给 sklearn,报告易流于"做了白做" | Spark 位置从"模型训练"挪到 **actigraphy 时序预处理**:滑窗聚合、统计特征抽取、群体 baseline 计算等阶段的数据量是数 GB 级,Spark 真实有收益 | 报告结论从"Spark 慢"变成"Spark 在 X 场景有收益,在 Y 场景无收益",科学性和深度都提升 |
| **O3** | 环境锁 `PyTorch 2.7.x + cu128`(来自 2025-04 信息,今天已过时);且未处理 5060 Ti 的 sm_120 适配 | 分三套环境矩阵:`mlsys_cpu (3.11)` / `mlsys_gpu_local (3.11 + torch 2.10+ nightly + cu128)` / `mlsys_gpu_remote (3.11 + torch 2.11 stable + cu128)` | 2026-04 的 sm_120 兼容不再临时救火;远程训练不用被 nightly 不稳定拖累 |
| **O4** | 66 GiB 可用磁盘无预算表,容易开题两周后磁盘爆 | 列出 7 项具体占用(PIU 原始 12 GiB / actigraphy parquet 5 GiB / 特征 2 GiB / MLflow 5 GiB / Checkpoint 2 GiB / Spark shuffle 10 GiB / conda 三份 15 GiB)合计 ~51 GiB,留 15 GiB 冗余;超预算自动切 WISDM | 事前有预算、事中有告警、事后有降级路径,不出现"差 3 GB 跑不完"的阻塞事故 |
| **O5** | 评价指标在 4 份 v1 方案里不一致:Accuracy / Macro-F1 / Weighted-F1 / QWK / LogLoss 五选混用 | P1 主指标锁 **Macro-F1** + 辅 QWK/Balanced Accuracy;P2 主指标锁 **QWK** + 辅 Macro-F1/LogLoss;两项目共用同一套系统指标(训练时/推理时/RSS/模型大小/特征处理时) | 答辩被问"主指标是什么"能一句话答;跨方案横向对比有公共尺子;`Weighted-F1` 在类别不平衡下易被 majority class 主导,已移除 |
| **O6** | 6 份 v1 子方案并列维护,信息过载,迭代阻力大 | 收敛为"1 份主线执行版(PIU)"+"备选摘要内嵌在 `06_risk_and_eval_v2.md`";其余 4 份降级为只读归档 | 精力聚焦,文档可维护;选题过程不丢失(归档仍在) |
| **O7** | v1 数据获取只写 URL,没给 Kaggle API 配置、下载命令、镜像 fallback、checksum | `05_runbook_v2.md` 里给出完整命令: `pip install kaggle` → 放 `kaggle.json` → `kaggle competitions download -c child-mind-institute-problematic-internet-use` → 校验 md5 → 镜像 fallback 两条 | 新成员开机即可跑;Kaggle 竞赛页 CDN 抽风时有 backup |
| **O8** | MLOps 只做到 MLflow + ModelScope 两件事,深度不够,答辩时不具备"完整 MLOps 闭环"说服力 | 扩展为 6 件套: (1) `MLflow Tracking + Registry` (2) `DVC` 管数据版本(或 git-lfs + dataset hash)(3) `Dockerfile` 两镜像(CPU 推理 / GPU 训练)(4) `FastAPI` 推理服务 `/predict` (5) `Makefile` 串起数据→训练→评估→注册→发布 (6) `ModelScope` 主仓 + `HuggingFace Hub` 镜像仓 | 答辩时 MLOps 完整度明显超出一般课程项目,且每一件都有落地命令,不是口号 |
| **O9** | 远程 4090 "使用窗口未知",无任何 fallback 时的方案 | 三级 GPU fallback: (Tier-1) 远程 4090 / (Tier-2) Kaggle Notebook 免费 T4×2 30h/周 / (Tier-3) AutoDL 按需 + Colab Pro;每级都给出 `mlsys_gpu_remote` 环境同步脚本 | 哪怕 4090 完全拿不到,项目依然能跑完;风险预期对齐到"最坏情况" |
| **O10** | `Weighted-F1` 在 charter 里作为主指标候选 | 已剔除,原因已在 O5 说明 | 指标选型更专业,答辩经得起问 |
| **O11** | 团队分工"3 人或 2 人两种写法并列",每个成员的周级产出无 | 锁 3 人,每人给出 W0-W9 的阶段性产出清单和 done 定义 | 进度可 review,责任可追溯 |
| **O12** | 时间计划止于"第一阶段 / 第二阶段"层级,颗粒度太粗 | 改成 **10 周的周历**(W0-W9),包含两个硬锚点(中期答辩 W4、最终答辩 W9)和每周验收标准 | 进度管理可度量;预警空间从"月"压到"周" |
| **O13** | v1 缺少 `actigraphy` 数据缺失的应对策略(web 搜索已确认 actigraphy 大量缺失) | 在 P1/P2 中明确: (a) 用全体参与者做 tabular 主线 (b) actigraphy 作"可选加强"分支,允许部分样本无 actigraphy (c) 融合模型用 late fusion,支持单分支输入 | 把"数据质量缺陷"从风险变成"设计决策",答辩反而有东西讲 |
| **O14** | v1 portfolio 引用 `scce.ucas.ac.cn` 当作"学位论文通用规范"来源,实为计算机学院页面 | 移除该引用,统一使用 `onestop.ucas.ac.cn` 开题/中期一站式通知和 `aipt.ucas.ac.cn` 人工智能学院通知作为参考 | 引用准确,答辩时不会被导师挑引用来源的毛病 |

### 5.1 其它增强点(小改动,合并成一条)

- 每个 v2 文件顶部都有"**相对 v1 改动点**"段,便于课程组快速 diff。
- P1/P2 都明确写了"**done 标准**",即这份作业达到什么状态算完。
- `runbook` 里给出完整 `conda create` 命令与 `requirements-pinned.txt`,不用手动查版本。
- 引入 `seed` 全局约定(42),保证可复现;跨系统比较要求种子一致。

## 6. 阅读本 v2/ 目录的推荐顺序

1. 本文档(`01_overview_v2.md`):5 分钟把握全局。
2. `02_charter_v2.md`:20 分钟看选题、命名、环境、里程碑。
3. `05_runbook_v2.md`:20 分钟知道"怎么开机"(装环境、下数据)。
4. `03_plan_p1_v2.md`:40 分钟看 P1 的实验设计与 Spark 价值点。
5. `04_plan_p2_v2.md`:40 分钟看 P2 的 MLOps 全流程与双发布。
6. `06_risk_and_eval_v2.md`:15 分钟熟悉"出事了怎么办"。

## 7. 本 v2 方案没有解决的事

诚实列出(避免过度许诺):

- **远程 4090 使用窗口依旧未确认**:只给了 fallback,没给保证。需要组员尽快联系机器管理员锁定时段。
- **actigraphy 原始数据在本地 31 GiB RAM 下的全量加载是否 OOM,未经实测**:计划 W0 完成一次 10% 抽样实验确认,若 OOM 就强制走 Spark 流式。
- **Kaggle API 在国内可能偶发连接失败**:已列镜像 fallback,但若全线失败只能走手动下载上传。
- **ModelScope 自定义模型仓库对"时序+tabular 双输入"的模板缺失**:需按 `custom pipeline` 走,可能需要 3-5 天额外封装工作;已在 W7 预留窗口。
- **中期答辩日期未确认**:按往届经验放在 5 月下旬,若学校另行通知需整体前移。

## 8. 修订记录

- `v2 | 2026-04-18`:首版优化方案总览,落地 D1/D2/D3 三项决策,产出 v2/ 目录 6 份文件。

## 9. 参考

- `00_docs/v1/mlsys_project_charter_v1.md`(评审基线)
- `00_docs/v1/kaggle_competition_candidates_v1.md`
- `00_docs/v1/plans/*_v1.md`(6 份)
- `00_docs/v1/memos/*_v1.md`(5 份)
- Kaggle PIU 竞赛页: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use
- PyTorch 2.11 Release: https://pytorch.org/blog/
- PyTorch on sm_120 追踪 issue: https://github.com/pytorch/pytorch/issues/164342
- NVIDIA Blackwell 软件迁移指南: https://forums.developer.nvidia.com/t/software-migration-guide-for-nvidia-blackwell-rtx-gpus/321330
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- ModelScope: https://github.com/modelscope/modelscope
- HuggingFace Hub: https://huggingface.co/docs/hub/
